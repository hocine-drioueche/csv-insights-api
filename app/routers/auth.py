from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import create_token_for_user, get_session
from app.models import UserDB
from app.schemas import LoginData

router = APIRouter(tags=["auth"])


@router.post("/login")
def login(login_data: LoginData, db: Session = Depends(get_session)):
    user = db.query(UserDB).filter(UserDB.username == login_data.username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "access_token": create_token_for_user(user.id),
        "token_type": "bearer",
    }