"""
Session Model - Data layer for coding sessions
Following MVC pattern: Models define data structure and business rules
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class CodingSession(Base):
    """Represents a learner's coding session with real-time analysis"""

    __tablename__ = "coding_sessions"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Session identification
    user_id = Column(String(255), nullable=False, index=True)  # Future multi-user support
    session_token = Column(String(255), unique=True, nullable=False, index=True)

    # Session metadata
    language = Column(String(50), nullable=False, default="python")
    problem_id = Column(String(255), ForeignKey("problems.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    ended_at = Column(DateTime, nullable=True)

    # Session state
    is_active = Column(Boolean, default=True, nullable=False)
    current_code = Column(Text, nullable=True)  # Latest code snapshot

    # Settings and configuration
    hint_level_preference = Column(Integer, default=1, nullable=False)  # H1-H4
    screen_mode_enabled = Column(Boolean, default=False, nullable=False)
    auto_analysis_enabled = Column(Boolean, default=True, nullable=False)

    # Performance metrics
    total_hints_requested = Column(Integer, default=0, nullable=False)
    errors_fixed = Column(Integer, default=0, nullable=False)
    session_duration_minutes = Column(Integer, default=0, nullable=False)

    # JSON fields for flexible data
    settings = Column(JSON, nullable=True)  # User preferences, UI state
    metadata = Column(JSON, nullable=True)  # Analytics, debugging info

    # Relationships
    problem = relationship("Problem", back_populates="sessions")
    analyses = relationship("CodeAnalysis", back_populates="session", cascade="all, delete-orphan")
    hints = relationship("MentorHint", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<CodingSession(id={self.id}, user_id={self.user_id}, language={self.language})>"


class Problem(Base):
    """Built-in problem bank with test cases for logic error detection"""

    __tablename__ = "problems"

    # Primary key
    id = Column(String(255), primary_key=True)  # e.g., "fibonacci_basic", "palindrome_check"

    # Problem content
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(20), nullable=False)  # "beginner", "intermediate", "advanced"
    category = Column(String(100), nullable=False)  # "algorithms", "data_structures", etc.

    # Test cases for verification
    test_cases = Column(JSON, nullable=False)  # [{"input": {...}, "expected": {...}, "description": "..."}]
    starter_code = Column(Text, nullable=True)  # Optional template
    solution_code = Column(Text, nullable=True)  # Reference solution

    # Metadata
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Statistics
    times_attempted = Column(Integer, default=0, nullable=False)
    average_completion_time = Column(Integer, nullable=True)  # Minutes

    # Relationships
    sessions = relationship("CodingSession", back_populates="problem")

    def __repr__(self) -> str:
        return f"<Problem(id={self.id}, title={self.title}, difficulty={self.difficulty})>"


class CodeAnalysis(Base):
    """Real-time analysis results from parsers, linters, and sandbox execution"""

    __tablename__ = "code_analyses"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key
    session_id = Column(Integer, ForeignKey("coding_sessions.id"), nullable=False, index=True)

    # Analysis metadata
    analysis_type = Column(String(50), nullable=False)  # "syntax", "lint", "execution", "logic"
    analyzer_name = Column(String(100), nullable=False)  # "ast_parser", "pylint", "mypy", "sandbox"

    # Code snapshot
    code_snapshot = Column(Text, nullable=False)
    code_hash = Column(String(64), nullable=False, index=True)  # For deduplication

    # Analysis results
    findings = Column(JSON, nullable=False)  # Structured results from analyzer
    severity = Column(String(20), nullable=False)  # "info", "warning", "error", "critical"
    is_blocking = Column(Boolean, default=False, nullable=False)  # Prevents code execution

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Status tracking
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("CodingSession", back_populates="analyses")
    hints = relationship("MentorHint", back_populates="analysis")

    def __repr__(self) -> str:
        return f"<CodeAnalysis(id={self.id}, type={self.analysis_type}, severity={self.severity})>"


class MentorHint(Base):
    """AI mentor hints with progressive disclosure (H1-H4 levels)"""

    __tablename__ = "mentor_hints"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    session_id = Column(Integer, ForeignKey("coding_sessions.id"), nullable=False, index=True)
    analysis_id = Column(Integer, ForeignKey("code_analyses.id"), nullable=True, index=True)

    # Hint metadata
    hint_level = Column(Integer, nullable=False)  # 1-4 (H1-H4)
    hint_category = Column(String(100), nullable=False)  # "syntax", "logic", "style", "performance"

    # Hint content
    hint_text = Column(Text, nullable=False)
    hint_type = Column(String(50), nullable=False)  # "suggestion", "question", "example", "solution"

    # LLM generation metadata
    llm_provider = Column(String(50), nullable=False)  # "local", "hosted"
    llm_model = Column(String(100), nullable=False)
    prompt_hash = Column(String(64), nullable=False)  # For caching/dedup
    generation_time_ms = Column(Integer, nullable=True)

    # User interaction
    was_helpful = Column(Boolean, nullable=True)  # User feedback
    user_reaction = Column(String(20), nullable=True)  # "helpful", "confusing", "incorrect"

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    shown_at = Column(DateTime, nullable=True)

    # Safety and quality
    safety_approved = Column(Boolean, default=False, nullable=False)
    contains_solution = Column(Boolean, default=False, nullable=False)  # H4 only

    # Relationships
    session = relationship("CodingSession", back_populates="hints")
    analysis = relationship("CodeAnalysis", back_populates="hints")

    def __repr__(self) -> str:
        return f"<MentorHint(id={self.id}, level=H{self.hint_level}, category={self.hint_category})>"