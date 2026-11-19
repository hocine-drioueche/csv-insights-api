from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Any

from app.models import AnalysisStatus


class LoginData(BaseModel):
    username: str


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


class AnalysisListItem(BaseModel):
    """Vue courte : utilisée par GET /analyses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    status: AnalysisStatus
    created_at: datetime


class AnalysisDetail(AnalysisListItem):
    """Vue complète : utilisée par GET /analyses/{id}."""
    file_size: int
    rows_count: int | None = None
    columns_count: int | None = None
    columns: list[str] | None = None
    stats_summary: dict[str, Any] | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
    owner_id: int


class AnalysisStats(BaseModel):
    """Résumé global : utilisé par GET /analyses/stats/summary."""
    total_files: int
    total_rows_processed: int