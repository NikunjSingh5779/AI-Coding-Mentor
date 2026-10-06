"""Persistent entities for sessions, analyses, problems and mentor hints."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Declarative base for the application."""


class CodingSession(Base):
    __tablename__ = "coding_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    session_token: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    language: Mapped[str] = mapped_column(String(50), default="python")
    problem_id: Mapped[str | None] = mapped_column(
        ForeignKey("problems.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    current_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    hint_level_preference: Mapped[int] = mapped_column(Integer, default=1)
    screen_mode_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_analysis_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    total_hints_requested: Mapped[int] = mapped_column(Integer, default=0)
    errors_fixed: Mapped[int] = mapped_column(Integer, default=0)
    session_duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    session_metadata: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    problem: Mapped["Problem | None"] = relationship(
        back_populates="sessions"
    )
    analyses: Mapped[list["CodeAnalysis"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    hints: Mapped[list["MentorHint"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(20))
    category: Mapped[str] = mapped_column(String(100))
    test_cases: Mapped[list] = mapped_column(JSON)
    starter_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    solution_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    times_attempted: Mapped[int] = mapped_column(Integer, default=0)
    average_completion_time: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    sessions: Mapped[list[CodingSession]] = relationship(
        back_populates="problem"
    )


class CodeAnalysis(Base):
    __tablename__ = "code_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("coding_sessions.id"), index=True
    )
    analysis_type: Mapped[str] = mapped_column(String(50))
    analyzer_name: Mapped[str] = mapped_column(String(100))
    analysis_time_ms: Mapped[float | None] = mapped_column(nullable=True)
    code_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    code_hash: Mapped[str] = mapped_column(String(64), index=True)
    findings: Mapped[list | dict] = mapped_column(JSON)
    severity: Mapped[str] = mapped_column(String(20))
    is_blocking: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    session: Mapped[CodingSession] = relationship(back_populates="analyses")
    hints: Mapped[list["MentorHint"]] = relationship(
        back_populates="analysis"
    )


class MentorHint(Base):
    __tablename__ = "mentor_hints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("coding_sessions.id"), index=True
    )
    analysis_id: Mapped[int | None] = mapped_column(
        ForeignKey("code_analyses.id"), nullable=True, index=True
    )
    hint_level: Mapped[int] = mapped_column(Integer)
    hint_category: Mapped[str] = mapped_column(String(100))
    hint_text: Mapped[str] = mapped_column(Text)
    hint_type: Mapped[str] = mapped_column(String(50), default="suggestion")
    llm_provider: Mapped[str] = mapped_column(String(50), default="template")
    llm_model: Mapped[str] = mapped_column(String(100), default="template")
    prompt_hash: Mapped[str] = mapped_column(String(64))
    generation_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    was_helpful: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    user_reaction: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    shown_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    safety_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    contains_solution: Mapped[bool] = mapped_column(Boolean, default=False)

    session: Mapped[CodingSession] = relationship(back_populates="hints")
    analysis: Mapped[CodeAnalysis | None] = relationship(back_populates="hints")


__all__ = ["Base", "CodeAnalysis", "CodingSession", "MentorHint", "Problem"]
