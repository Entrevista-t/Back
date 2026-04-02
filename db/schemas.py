from pydantic import BaseModel, EmailStr
from datetime import datetime

# 1. Base: Camps comuns que sempre es repeteixen
class UsuariBase(BaseModel):
    nom: str
    email: EmailStr  # Això validarà automàticament que tingui format de correu (@ i .com)

# 2. Schema per CREAR un usuari (el que rep l'API des del frontend)
class UsuariCreate(UsuariBase):
    password: str

# 3. Schema per RETORNAR un usuari (el que l'API envia al frontend)
class UsuariResponse(UsuariBase):
    id: int
    data_creacio: datetime

    # Aquesta configuració permet que Pydantic llegeixi directament dels models de SQLAlchemy
    model_config = {"from_attributes": True}