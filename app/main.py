from fastapi import FastAPI

from app.database import Base, SessionLocal, engine
from app.models import UserDB
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router

app = FastAPI(title="CSV Insights API")

Base.metadata.create_all(bind=engine)


def seed_data():
    db = SessionLocal()
    try:
        if db.query(UserDB).count() == 0:
            db.add_all([UserDB(username="alice"), UserDB(username="bob")])
            db.commit()
    finally:
        db.close()


seed_data()

app.include_router(auth_router)
app.include_router(users_router)


@app.get("/health")
def health():
    return {"status": "ok"}