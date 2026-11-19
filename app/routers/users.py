from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_session
from app.models import UserDB
from app.schemas import User

router = APIRouter(tags=["users"])


@router.get("/users", response_model=list[User])
def get_users(
    db: Session = Depends(get_session),
    current_user: UserDB = Depends(get_current_user),
):
    return db.query(UserDB).order_by(UserDB.id).all()