from __future__ import annotations

import hashlib
import time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.mentor.adaptation import recommend_hint_level
from app.mentor.client import MentorClient, MentorProviderError, extract_json_object
from app.mentor.prompts import build_prompt
from app.mentor.redaction import safe_hint_text
from app.mentor.templates import template_hint
from app.models.session import CodeAnalysis, CodingSession, MentorHint

class MentorService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = MentorClient(
            settings.llm_base_url,
            settings.llm_api_key,
            settings.llm_model,
            settings.llm_timeout,
        )

    async def request_hint(
        self,
        db: AsyncSession,
        *,
        session: CodingSession,
        analysis: CodeAnalysis | None,
        requested_level: int | None,
        allow_solution: bool,
        code: str = "",
        diagnostic_dicts: list[dict] | None = None,
    ) -> dict:
        if requested_level is not None and requested_level not in {1, 2, 3, 4}:
            raise ValueError("hint_level must be between 1 and 4")

        prior_count = int(
            await db.scalar(
                select(func.count(MentorHint.id)).where(
                    MentorHint.session_id == session.id
                )
            ) or 0
        )
        if prior_count >= self.settings.mentor_max_hints_per_session:
            raise ValueError("Mentor hint limit reached")

        diagnostics = []
        source_findings = diagnostic_dicts
        if source_findings is None and analysis and isinstance(analysis.findings, list):
            source_findings = analysis.findings
        if source_findings:
            from app.schemas.diagnostic import Diagnostic
            for item in source_findings:
                try:
                    diagnostics.append(Diagnostic.model_validate(item))
                except Exception:
                    continue

        level = requested_level or recommend_hint_level(
            diagnostics,
            prior_hint_count=prior_count,
            adaptive_enabled=self.settings.adaptive_enabled,
        )
        if level == 4 and not allow_solution:
            raise PermissionError("H4 requires explicit confirmation")

        code = safe_hint_text(code or session.current_code or "", 16000, True)
        category = diagnostics[0].category if diagnostics else "LOGIC_SUSPICION"
        prompt_hash = hashlib.sha256(
            f"{session.id}|{analysis.id if analysis else 0}|{level}|{code}".encode()
        ).hexdigest()

        cached = await db.scalar(
            select(MentorHint).where(
                MentorHint.session_id == session.id,
                MentorHint.prompt_hash == prompt_hash,
                MentorHint.hint_level == level,
            )
        )
        if cached:
            return self.serialize(cached)

        started = time.perf_counter()
        provider = "template"
        model = "template"
        hint = template_hint(category, level)

        if self.settings.llm_enabled:
            try:
                raw = await self.client.generate(
                    build_prompt(
                        code,
                        diagnostics,
                        level,
                        allow_solution=allow_solution,
                    ),
                    max_tokens=self.settings.llm_max_tokens,
                    temperature=self.settings.llm_temperature,
                )
                payload = extract_json_object(raw)
                hint = safe_hint_text(
                    str(payload.get("hint", hint)),
                    self.settings.mentor_max_hint_chars,
                    allow_solution,
                )
                provider = self.settings.llm_provider
                model = self.settings.llm_model
            except (MentorProviderError, ValueError, TypeError, KeyError):
                pass

        record = MentorHint(
            session_id=session.id,
            analysis_id=analysis.id if analysis else None,
            hint_level=level,
            hint_category=category,
            hint_text=hint,
            hint_type="solution" if level == 4 else "suggestion",
            llm_provider=provider,
            llm_model=model,
            prompt_hash=prompt_hash,
            generation_time_ms=int((time.perf_counter() - started) * 1000),
            safety_approved=True,
            contains_solution=(level == 4 and allow_solution),
        )
        db.add(record)
        session.total_hints_requested += 1
        await db.flush()
        return self.serialize(record)

    @staticmethod
    def serialize(hint: MentorHint) -> dict:
        return {
            "id": hint.id,
            "hint_level": hint.hint_level,
            "hint_category": hint.hint_category,
            "hint_text": hint.hint_text,
            "hint_type": hint.hint_type,
            "provider": hint.llm_provider,
            "model": hint.llm_model,
            "generation_time_ms": hint.generation_time_ms,
            "safety_approved": hint.safety_approved,
            "contains_solution": hint.contains_solution,
            "created_at": hint.created_at.isoformat() if hint.created_at else None,
        }
