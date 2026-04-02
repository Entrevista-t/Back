from pydantic import BaseModel, EmailStr
from datetime import datetime

class UsuariBase(BaseModel):
    nom: str
    email: EmailStr

class UsuariCreate(UsuariBase):
    password: str

class UsuariResponse(UsuariBase):
    id: int
    data_creacio: datetime

    model_config = {"from_attributes": True}