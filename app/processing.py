import io
from datetime import datetime, timezone

import pandas as pd

from app.database import SessionLocal
from app.models import AnalysisDB, AnalysisStatus


def _to_python(value) -> float | None:
    """NaN -> None et types numpy -> float Python, pour que ce soit sérialisable en JSON."""
    return None if pd.isna(value) else float(value)


def build_stats_summary(df: pd.DataFrame) -> dict:
    summary = {}
    for column in df.columns:
        series = df[column]
        info = {"type": str(series.dtype)}

        is_numeric = pd.api.types.is_numeric_dtype(series)
        is_bool = pd.api.types.is_bool_dtype(series)
        if is_numeric and not is_bool:
            info["describe"] = {
                key: _to_python(value) for key, value in series.describe().items()
            }

        summary[str(column)] = info
    return summary


def process_analysis(analysis_id: int, content: bytes) -> None:
    db = SessionLocal()
    try:
        analysis = db.get(AnalysisDB, analysis_id)
        if analysis is None:  # supprimée entre-temps
            return

        analysis.status = AnalysisStatus.running
        db.commit()


        try:
            df = pd.read_csv(io.BytesIO(content))

            analysis.rows_count = len(df)
            analysis.columns_count = len(df.columns)
            analysis.columns = [str(c) for c in df.columns]
            analysis.stats_summary = build_stats_summary(df)
            analysis.status = AnalysisStatus.completed
        except Exception as exc:
            db.rollback()
            analysis.status = AnalysisStatus.failed
            analysis.error_message = str(exc)

        analysis.finished_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()