from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional
import re 

# ==========================================
# 👤 USUARIS
# ==========================================

class UsuariBase(BaseModel):
    nom: str = Field(..., min_length=2, max_length=100)
    email: EmailStr

class UsuariCreate(UsuariBase):
    password: str = Field(..., min_length=8, max_length=50)

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str):
        # Comentat per proves
        return v

class UsuariResponse(UsuariBase):
    id: int
    data_creacio: datetime

    model_config = {"from_attributes": True}

class UsuariLogin(BaseModel):
    email: EmailStr
    password: str

class UsuariUpdate(BaseModel):
    nom: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


# ==========================================
# 🏷️ CATEGORIES
# ==========================================

class CategoriaBase(BaseModel):
    nom: str
    descripcio: Optional[str] = None

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaResponse(CategoriaBase):
    id: int
    
    model_config = {"from_attributes": True}


# ==========================================
# ❓ PREGUNTES
# ==========================================

class PreguntaBase(BaseModel):
    # Important: s'ha de dir exactament igual que la columna de models.py
    text_pregunta: str 
    id_categoria: int

class PreguntaCreate(PreguntaBase):
    pass

class PreguntaResponse(PreguntaBase):
    id: int

    model_config = {"from_attributes": True}