from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import re # for field_validator

class UsuariBase(BaseModel):
    nom: str = Field(..., min_length=2, max_length=100)
    email: EmailStr

class UsuariCreate(UsuariBase):
    password: str = Field(..., min_length=8, max_length=50)

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str):
        #comentem això de moment per poder-ho provar més fàcilment

        #if not any(char.isdigit() for char in v):
        #    raise ValueError('La contrasenya ha de contenir almenys un número.')
        
        #if not any(char.isupper() for char in v):
        #    raise ValueError('La contrasenya ha de contenir almenys una lletra majúscula.')
        
        #if not any(char.islower() for char in v):
        #    raise ValueError('La contrasenya ha de contenir almenys una lletra minúscula.')
        
        #if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
        #    raise ValueError('La contrasenya ha de contenir almenys un caràcter especial.')
        
            
        return v

class UsuariResponse(UsuariBase):
    id: int
    data_creacio: datetime

    model_config = {"from_attributes": True}

class UsuariLogin(BaseModel):
    email: EmailStr
    password: str
    