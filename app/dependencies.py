import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import UserDB

security = HTTPBearer()

# token -> user_id (en mémoire, perdu au redémarrage)
tokens: dict[str, int] = {}


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_token_for_user(user_id: int) -> str:
    token = secrets.token_hex(16)
    tokens[token] = user_id
    return token


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_session),
) -> UserDB:
    user_id = tokens.get(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user