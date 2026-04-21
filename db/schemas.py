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
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v

class UsuariResponse(UsuariBase):
    id: int
    data_creacio: datetime
    url_foto: Optional[str] = None

    model_config = {"from_attributes": True}

class UsuariLogin(BaseModel):
    email: EmailStr
    password: str

class UsuariUpdate(BaseModel):
    nom: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=50)
    url_foto: Optional[str] = None

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        if v is None:
            return v
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v


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

class CategoriaUpdate(BaseModel):
    nom: Optional[str] = None
    descripcio: Optional[str] = None


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

class PreguntaUpdate(BaseModel):
    text_pregunta: Optional[str] = None
    id_categoria: Optional[int] = None

# ==========================================
# 🎥 ENTREVISTES
# ==========================================

class EntrevistaBase(BaseModel):
    id_pregunta: Optional[int] = None

class EntrevistaCreate(EntrevistaBase):
    # Quan l'usuari tria una pregunta per començar, només ens envia el seu ID
    pass

class EntrevistaResponse(EntrevistaBase):
    id: int
    id_usuari: int
    data_hora: datetime
    url_video: Optional[str] = None
    url_informe_pdf: Optional[str] = None
    estat_proces: str
    metriques: Optional[dict] = None # Recorda que a models.py és JSONB

    model_config = {"from_attributes": True}