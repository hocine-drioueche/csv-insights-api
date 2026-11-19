import enum
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Integer, String

from app.database import Base


class AnalysisStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, unique=True)


class AnalysisDB(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, nullable=False)
    status = Column(
        Enum(AnalysisStatus),
        nullable=False,
        default=AnalysisStatus.pending,
    )
    file_size = Column(Integer, nullable=False)

    # Renseignés plus tard par la tâche de fond
    rows_count = Column(Integer, nullable=True)
    columns_count = Column(Integer, nullable=True)
    columns = Column(JSON, nullable=True)
    stats_summary = Column(JSON, nullable=True)

    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    finished_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)