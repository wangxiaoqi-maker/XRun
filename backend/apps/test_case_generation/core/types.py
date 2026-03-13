from enum import Enum


class SessionStatus(Enum):
    PENDING = "pending"
    PARSING = "parsing"
    EXTRACTING_POINTS = "extracting_points"
    POINTS_PENDING_REVIEW = "points_pending_review"
    GENERATING_CASES = "generating_cases"
    CASES_PENDING_REVIEW = "cases_pending_review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReviewStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class TestMethod(Enum):
    EQUIVALENCE_PARTITIONING = "equivalence_partitioning"
    BOUNDARY_VALUE = "boundary_value"
    ERROR_GUESSING = "error_guessing"
    SCENARIO_BASED = "scenario_based"
    DECISION_TABLE = "decision_table"
    STATE_TRANSITION = "state_transition"
    COMPREHENSIVE = "comprehensive"


class InputSourceType(Enum):
    DOCUMENT = "document"
    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"
    HISTORY = "history"
    KNOWLEDGE = "knowledge"


class FileStatus(Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    ERROR = "error"
