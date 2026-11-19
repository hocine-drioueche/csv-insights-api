from pathlib import Path

from fastapi import APIRouter, BackgroundTasks,Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_session
from app.models import AnalysisDB, UserDB
from app.schemas import AnalysisListItem
from app.processing import process_analysis
from app.schemas import AnalysisDetail, AnalysisListItem

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post(
    "/upload",
    response_model=AnalysisListItem,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_analysis(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    # Path(...).name garde seulement le nom, sans dossier éventuel
    file_name = Path(file.filename or "").name

    if not file_name.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only CSV files are allowed",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    analysis = AnalysisDB(
        file_name=file_name,
        file_size=len(content),
        owner_id=current_user.id,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    background_tasks.add_task(process_analysis, analysis.id, content)

    return analysis


@router.get("", response_model=list[AnalysisListItem])
def list_analyses(
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    return db.query(AnalysisDB).order_by(AnalysisDB.id).all()


@router.get("/{analysis_id}", response_model=AnalysisDetail)
def get_analysis(
    analysis_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    analysis = db.get(AnalysisDB, analysis_id)

    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return analysis