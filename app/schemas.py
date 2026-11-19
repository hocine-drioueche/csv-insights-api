from pydantic import BaseModel, ConfigDict


class LoginData(BaseModel):
    username: str


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str