from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.mentor.redaction import redact_secrets
from app.models.session import CodeAnalysis, CodingSession, Problem
from app.schemas.diagnostic import Diagnostic


async def get_session(db: AsyncSession, token: str) -> CodingSession | None:
    return await db.scalar(
        select(CodingSession).where(CodingSession.session_token == token)
    )


async def record_analysis(
    db: AsyncSession,
    session: CodingSession,
    *,
    code: str,
    diagnostics: list[Diagnostic],
    timings: dict[str, float],
    settings: Settings,
    analysis_type: str = "fast_static",
) -> CodeAnalysis:
    previous = await db.scalar(
        select(CodeAnalysis)
        .where(CodeAnalysis.session_id == session.id)
        .order_by(CodeAnalysis.created_at.desc())
        .limit(1)
    )
    current_fingerprints = {
        d.fingerprint for d in diagnostics if d.fingerprint
    }
    previous_fingerprints = set()
    if previous and isinstance(previous.findings, list):
        previous_fingerprints = {
            str(item.get("fingerprint"))
            for item in previous.findings
            if isinstance(item, dict) and item.get("fingerprint")
        }

    fixed = len(previous_fingerprints - current_fingerprints) if previous else 0
    session.errors_fixed += fixed

    findings = [
        {
            "id": d.id,
            "seq": d.seq,
            "origin": d.origin.value,
            "rule": d.rule,
            "category": d.category,
            "severity": d.severity.value,
            "message_raw": redact_secrets(d.message_raw),
            "range": {
                "start": {"line": d.range.start.line, "col": d.range.start.col},
                "end": {"line": d.range.end.line, "col": d.range.end.col},
            },
            "fingerprint": d.fingerprint,
            "confidence": d.confidence,
        }
        for d in diagnostics
    ]

    severity = (
        "error"
        if any(d.severity.value == "error" for d in diagnostics)
        else "warning"
        if any(d.severity.value == "warning" for d in diagnostics)
        else "info"
    )
    record = CodeAnalysis(
        session_id=session.id,
        analysis_type=analysis_type,
        analyzer_name="analysis-pipeline",
        code_snapshot=(
            redact_secrets(code) if settings.store_code_text else None
        ),
        code_hash=hashlib.sha256(code.encode("utf-8")).hexdigest(),
        findings=findings,
        severity=severity,
        is_blocking=severity == "error",
        analysis_time_ms=float(timings.get("total", 0.0)),
    )
    db.add(record)
    await db.flush()
    return record


async def seed_problems(db: AsyncSession, problems: list[dict]) -> None:
    for payload in problems:
        existing = await db.get(Problem, payload["id"])
        if existing is None:
            db.add(
                Problem(
                    id=payload["id"],
                    title=payload["title"],
                    description=payload["description"],
                    difficulty=payload["difficulty"],
                    category=payload["category"],
                    test_cases=payload["test_cases"],
                    starter_code=payload.get("starter_code"),
                    solution_code=payload.get("solution"),
                )
            )
    await db.flush()



async def cleanup_expired_sessions(
    db: AsyncSession,
    retention_days: int,
) -> int:
    """Delete completed sessions older than the configured retention window."""

    if retention_days <= 0:
        return 0
    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    result = await db.execute(
        select(CodingSession).where(
            CodingSession.is_active.is_(False),
            CodingSession.updated_at < cutoff,
        )
    )
    sessions = list(result.scalars())
    for session in sessions:
        await db.delete(session)
    await db.flush()
    return len(sessions)
