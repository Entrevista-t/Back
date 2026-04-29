from fastapi import Depends, FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import text, func
from sqlalchemy.orm import Session
from db.database import get_db, engine, Base
from db.models import Entrevista, Usuari, Categoria, Pregunta
from db.schemas import (
    EntrevistaCreate, EntrevistaResponse, UsuariCreate, UsuariResponse, UsuariLogin, UsuariUpdate,
    CategoriaCreate, CategoriaResponse, CategoriaUpdate,
    PreguntaCreate, PreguntaResponse, PreguntaUpdate
)
from interview_analyzer import analyze_interview
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import jwt
from jwt.exceptions import InvalidTokenError
import os
import asyncio
import tempfile
import logging
import shutil
import uuid
from pathlib import Path
from fastapi.staticfiles import StaticFiles

from fastapi.responses import FileResponse
from pdf_generator import generar_pdf_entrevista

#--------------------------------PASSWD HASHING CONTEXT--------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#--------------------------------FASTAPI APP & CONFIG--------------------------------

MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500 MB
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v", ".wmv"}

app = FastAPI(
    title="Entrevistat't API",
    description="Backend para el proyecto universitario",
    version="1.0.0"
)

# Configure CORS to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://entrevistat.kire.ovh", "http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],  # Allow frontend origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Serve uploaded profile pictures as static files
UPLOAD_DIR = Path("uploads/profile_pictures")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

def verify_password(plain_password, hashed_password):
    """Comprova si la contrasenya en text pla coincideix amb el hash de la BD."""
    return pwd_context.verify(plain_password, hashed_password)


@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse(url="/docs")

# ==========================================
# ⚙️ CONFIGURACIÓ OAUTH2 I JWT
# ==========================================

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
if not SECRET_KEY:
    logger.warning("JWT_SECRET_KEY not set — using insecure default for development only!")
    SECRET_KEY = "dev-only-insecure-default-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # Token lasts 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Generates the actual JWT token string."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """The Security Guard: Reads the token, validates it, and fetches the user from your DB."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
        
    user = db.query(Usuari).filter(Usuari.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

# ==========================================
# 🔐 AUTENTICACIÓ
# ==========================================

@app.post("/auth/register", response_model=UsuariResponse, status_code=status.HTTP_201_CREATED, tags=["Autenticació"])
def register(user: UsuariCreate, db: Session = Depends(get_db)):
    """Crea un compte nou (Registre)."""
    
    existing_user = db.query(Usuari).filter(Usuari.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="No s'ha pogut completar el registre."
        )

    hashed_password = get_password_hash(user.password)

    nou_usuari = Usuari(
        nom=user.nom,
        email=user.email,
        password=hashed_password
    )

    db.add(nou_usuari)
    db.commit()
    
    db.refresh(nou_usuari)

    return nou_usuari

@app.post("/auth/login", tags=["Autenticació"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Autentica l'usuari i retorna un token JWT (Login compatible amb Swagger)."""
    
    # IMPORTANT: El Swagger posa el nostre email dins del camp 'username' per defecte.
    # Per tant, busquem a la BD fent servir form_data.username
    user = db.query(Usuari).filter(Usuari.email == form_data.username).first()
    
    # Comprovem contrasenya
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contrasenya incorrectes",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Creem i retornem el token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


# ==========================================
# 👤 USUARIS (CRUD i Perfil)
# ==========================================

# NOTA IMPORTANT: '/usuarios/me' ha d'anar SEMPRE abans que '/usuarios/{id}' 
# perquè FastAPI llegeix de dalt a baix i podria confondre 'me' amb un ID.

@app.get("/usuarios/me", response_model=UsuariResponse, tags=["Usuaris"])
def get_current_user_profile(usuari_actual: Usuari = Depends(get_current_user)):
    """Retorna les dades del perfil de l'usuari autenticat actualment."""
    
    return usuari_actual


@app.post("/usuarios/me/foto", response_model=UsuariResponse, tags=["Usuaris"])
async def upload_profile_picture(
    foto: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuari_actual: Usuari = Depends(get_current_user)
):
    """Puja una foto de perfil per a l'usuari autenticat."""
    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if foto.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Tipus de fitxer no permès. Utilitza JPEG, PNG, WebP o GIF."
        )

    # Validate file size (max 5MB)
    contents = await foto.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="La imatge és massa gran. Màxim 5 MB."
        )

    # Generate unique filename
    ext = Path(foto.filename or "photo.jpg").suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = UPLOAD_DIR / filename

    # Delete old photo if exists
    if usuari_actual.url_foto:
        old_path = Path(usuari_actual.url_foto.lstrip("/"))
        if old_path.exists():
            old_path.unlink(missing_ok=True)

    # Save file
    with open(filepath, "wb") as f:
        f.write(contents)

    # Update user record
    usuari_actual.url_foto = f"/uploads/profile_pictures/{filename}"
    db.commit()
    db.refresh(usuari_actual)

    return usuari_actual


# Per crear usuaris internament
@app.post("/usuarios", response_model=UsuariResponse, status_code=status.HTTP_201_CREATED, tags=["Usuaris"])
def create_user(
    user: UsuariCreate, 
    db: Session = Depends(get_db),
    usuari_actual: Usuari = Depends(get_current_user) # 🔒 El Guàrdia de Seguretat!
):
    """
    Crea un nou usuari (ús intern). 
    A diferència del registre, necessites estar loguejat per fer servir això.
    """
    
    existing_user = db.query(Usuari).filter(Usuari.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Aquest email ja està registrat."
        )

    hashed_password = get_password_hash(user.password)

    nou_usuari = Usuari(
        nom=user.nom,
        email=user.email,
        password=hashed_password
    )

    db.add(nou_usuari)
    db.commit()
    db.refresh(nou_usuari)

    return nou_usuari

@app.get("/usuarios", response_model=List[UsuariResponse], tags=["Usuaris"])
def list_users(
    db: Session = Depends(get_db),
    usuari_actual: Usuari = Depends(get_current_user) # 🔒 Protegit
):
    """Llista tots els usuaris de la base de dades."""
    usuaris = db.query(Usuari).all()
    return usuaris

@app.get("/usuarios/{id}", response_model=UsuariResponse, tags=["Usuaris"])
def get_user(
    id: int, 
    db: Session = Depends(get_db),
    usuari_actual: Usuari = Depends(get_current_user) # 🔒 Protegit
):
    """Retorna els detalls d'un usuari específic buscant pel seu ID."""
    user = db.query(Usuari).filter(Usuari.id == id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuari no trobat"
        )
    return user

@app.put("/usuarios/{id}", response_model=UsuariResponse, tags=["Usuaris"])
def update_user_full(
    id: int, 
    user_in: UsuariCreate, # El PUT demana l'esquema de creació (tot obligatori)
    db: Session = Depends(get_db),
    usuari_actual: Usuari = Depends(get_current_user) # 🔒 Protegit
):
    """Reemplaça totes les dades d'un usuari. (Requereix enviar nom, email i password)."""
    if usuari_actual.id != id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tens permís per modificar aquest usuari.")

    user = db.query(Usuari).filter(Usuari.id == id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuari no trobat")
        
    user.nom = user_in.nom
    user.email = user_in.email
    user.password = get_password_hash(user_in.password)
    
    db.commit()
    db.refresh(user)
    return user

@app.patch("/usuarios/{id}", response_model=UsuariResponse, tags=["Usuaris"])
def update_user_partial(
    id: int, 
    user_in: UsuariUpdate, # El PATCH utilitza l'esquema on tot és opcional
    db: Session = Depends(get_db),
    usuari_actual: Usuari = Depends(get_current_user) # 🔒 Protegit
):
    """Modifica camps específics d'un usuari (pots enviar només el nom, per exemple)."""
    if usuari_actual.id != id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tens permís per modificar aquest usuari.")

    user = db.query(Usuari).filter(Usuari.id == id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuari no trobat")
        
    # Modifiquem NOMÉS els camps que ens han enviat al JSON
    if user_in.nom is not None:
        user.nom = user_in.nom
    if user_in.email is not None:
        user.email = user_in.email
    if user_in.password is not None:
        user.password = get_password_hash(user_in.password)
    if user_in.url_foto is not None:
        user.url_foto = user_in.url_foto
        
    db.commit()
    db.refresh(user)
    return user

@app.delete("/usuarios/{id}", tags=["Usuaris"])
def delete_user(
    id: int, 
    db: Session = Depends(get_db),
    usuari_actual: Usuari = Depends(get_current_user) # 🔒 Protegit
):
    """Elimina un usuari de la base de dades."""
    if usuari_actual.id != id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tens permís per eliminar aquest usuari.")

    user = db.query(Usuari).filter(Usuari.id == id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuari no trobat"
        )
        
    db.delete(user)
    db.commit()
    
    return {"message": f"Usuari amb ID {id} eliminat correctament"}

# ==========================================
# 🏷️ CATEGORIES
# ==========================================

@app.get("/categorias", response_model=List[CategoriaResponse], tags=["Categories"])
def list_categories(db: Session = Depends(get_db)):
    """Llista totes les categories disponibles a la base de dades."""
    categories = db.query(Categoria).all()
    return categories

@app.post("/categorias", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED, tags=["Categories"])
def create_category(
    categoria: CategoriaCreate, 
    db: Session = Depends(get_db),
    usuari_actual: Usuari = Depends(get_current_user) # 🔒 Protegit
):
    """Crea una nova categoria a la base de dades."""
    db_categoria = db.query(Categoria).filter(Categoria.nom == categoria.nom).first()
    if db_categoria:
        raise HTTPException(status_code=400, detail="Aquesta categoria ja existeix.")
    
    nova_categoria = Categoria(nom=categoria.nom, descripcio=categoria.descripcio)
    db.add(nova_categoria)
    db.commit()
    db.refresh(nova_categoria)
    return nova_categoria

@app.put("/categorias/{id}", response_model=CategoriaResponse, tags=["Categories"])
def update_category_full(
    id: int, 
    cat_in: CategoriaCreate, 
    db: Session = Depends(get_db),
    usuari_actual: Usuari = Depends(get_current_user) # 🔒 Protegit
):
    """Reemplaça completament una categoria (nom i descripció obligatoris)."""
    categoria = db.query(Categoria).filter(Categoria.id == id).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria no trobada")
    
    categoria.nom = cat_in.nom
    categoria.descripcio = cat_in.descripcio
    
    db.commit()
    db.refresh(categoria)
    return categoria

@app.patch("/categorias/{id}", response_model=CategoriaResponse, tags=["Categories"])
def update_category_partial(
    id: int, 
    cat_in: CategoriaUpdate, 
    db: Session = Depends(get_db),
    usuari_actual: Usuari = Depends(get_current_user) # 🔒 Protegit
):
    """Modifica parcialment una categoria (nom o descripció opcionals)."""
    categoria = db.query(Categoria).filter(Categoria.id == id).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria no trobada")
    
    if cat_in.nom is not None:
        categoria.nom = cat_in.nom
    if cat_in.descripcio is not None:
        categoria.descripcio = cat_in.descripcio
        
    db.commit()
    db.refresh(categoria)
    return categoria

@app.delete("/categorias/{id}", tags=["Categories"])
def delete_category(
    id: int, 
    db: Session = Depends(get_db),
    usuari_actual: Usuari = Depends(get_current_user) # 🔒 Protegit
):
    """Elimina una categoria. Les preguntes associades passaran a tenir la categoria NULL."""
    categoria = db.query(Categoria).filter(Categoria.id == id).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria no trobada")
    
    db.delete(categoria)
    db.commit()
    return {"message": f"Categoria '{categoria.nom}' eliminada correctament"}

# ==========================================
# ❓ PREGUNTES
# ==========================================

@app.post("/preguntas", response_model=PreguntaResponse, status_code=status.HTTP_201_CREATED, tags=["Preguntes"])
def create_question(
    pregunta: PreguntaCreate, 
    db: Session = Depends(get_db),
    usuari_actual: Usuari = Depends(get_current_user)
):
    """Afegeix una nova pregunta associada a una categoria."""
    
    # 1. Verifiquem que la categoria existeixi
    cat = db.query(Categoria).filter(Categoria.id == pregunta.id_categoria).first()
    if not cat:
        raise HTTPException(status_code=404, detail="La categoria especificada no existeix.")

    # 2. Creem la pregunta (COMPTE AQUÍ: fem servir text_pregunta)
    nova_pregunta = Pregunta(
        text_pregunta=pregunta.text_pregunta, 
        id_categoria=pregunta.id_categoria
    )
    
    # 3. Guardem a la base de dades
    db.add(nova_pregunta)
    db.commit()
    db.refresh(nova_pregunta)
    
    return nova_pregunta

@app.get("/preguntas", response_model=List[PreguntaResponse], tags=["Preguntes"])
def list_questions(
    categoria_id: Optional[int] = None, # 🔎 Això és un Query Parameter opcional
    db: Session = Depends(get_db)
):
    """
    Llista totes les preguntes. 
    Si li passes un categoria_id, només et retornarà les d'aquella categoria.
    """
    
    # Si ens han passat una categoria, filtrem
    if categoria_id:
        preguntes = db.query(Pregunta).filter(Pregunta.id_categoria == categoria_id).all()
    # Si no ens han passat res, les retornem totes
    else:
        preguntes = db.query(Pregunta).all()
        
    return preguntes

@app.get("/preguntas/random", response_model=PreguntaResponse, tags=["Preguntes"])
def get_random_question(
    categoria_id: int, 
    db: Session = Depends(get_db)
):
    """Retorna una pregunta aleatòria d'una categoria específica per començar l'entrevista."""
    
    # Busquem preguntes de la categoria i les ordenem a l'atzar
    pregunta = db.query(Pregunta).filter(Pregunta.id_categoria == categoria_id).order_by(func.random()).first()
    
    if not pregunta:
        raise HTTPException(
            status_code=404, 
            detail="No hi ha preguntes per a aquesta categoria o la categoria no existeix."
        )
        
    return pregunta

@app.put("/preguntas/{id}", response_model=PreguntaResponse, tags=["Preguntes"])
def update_question_full(
    id: int, 
    pregunta_in: PreguntaCreate, 
    db: Session = Depends(get_db),
    usuari_actual: Usuari = Depends(get_current_user)
):
    """Reemplaça completament una pregunta (text i categoria obligatoris)."""
    pregunta = db.query(Pregunta).filter(Pregunta.id == id).first()
    if not pregunta:
        raise HTTPException(status_code=404, detail="Pregunta no trobada")
    
    # Verifiquem que la nova categoria existeixi
    cat = db.query(Categoria).filter(Categoria.id == pregunta_in.id_categoria).first()
    if not cat:
        raise HTTPException(status_code=400, detail="La categoria especificada no existeix.")

    pregunta.text_pregunta = pregunta_in.text_pregunta
    pregunta.id_categoria = pregunta_in.id_categoria
    
    db.commit()
    db.refresh(pregunta)
    return pregunta

@app.patch("/preguntas/{id}", response_model=PreguntaResponse, tags=["Preguntes"])
def update_question_partial(
    id: int, 
    pregunta_in: PreguntaUpdate, 
    db: Session = Depends(get_db),
    usuari_actual: Usuari = Depends(get_current_user)
):
    """Modifica parcialment una pregunta (text o categoria opcionals)."""
    pregunta = db.query(Pregunta).filter(Pregunta.id == id).first()
    if not pregunta:
        raise HTTPException(status_code=404, detail="Pregunta no trobada")
    
    # Si ens canvien la categoria, mirem que existeixi
    if pregunta_in.id_categoria is not None:
        cat = db.query(Categoria).filter(Categoria.id == pregunta_in.id_categoria).first()
        if not cat:
            raise HTTPException(status_code=400, detail="La categoria especificada no existeix.")
        pregunta.id_categoria = pregunta_in.id_categoria

    if pregunta_in.text_pregunta is not None:
        pregunta.text_pregunta = pregunta_in.text_pregunta
        
    db.commit()
    db.refresh(pregunta)
    return pregunta

@app.delete("/preguntas/{id}", tags=["Preguntes"])
def delete_question(
    id: int, 
    db: Session = Depends(get_db),
    usuari_actual: Usuari = Depends(get_current_user)
):
    """Elimina una pregunta. Les entrevistes que la feien servir mantindran el registre però amb id_pregunta buit."""
    pregunta = db.query(Pregunta).filter(Pregunta.id == id).first()
    if not pregunta:
        raise HTTPException(status_code=404, detail="Pregunta no trobada")
    
    db.delete(pregunta)
    db.commit()
    return {"message": f"Pregunta amb ID {id} eliminada correctament"}


# ==========================================
# 🎥 ENTREVISTES
# ==========================================

@app.post("/entrevistas", response_model=EntrevistaResponse, status_code=status.HTTP_201_CREATED, tags=["Entrevistes"])
def create_interview(
    entrevista_in: EntrevistaCreate, 
    db: Session = Depends(get_db),
    usuari_actual: Usuari = Depends(get_current_user)
):
    """
    Crea un nou registre d'entrevista en estat 'pendent'.
    Es crida quan l'usuari accepta la pregunta i es disposa a gravar.
    """
    if entrevista_in.id_pregunta:
        pregunta = db.query(Pregunta).filter(Pregunta.id == entrevista_in.id_pregunta).first()
        if not pregunta:
            raise HTTPException(status_code=404, detail="La pregunta especificada no existeix.")

    nova_entrevista = Entrevista(
        id_usuari=usuari_actual.id,
        id_pregunta=entrevista_in.id_pregunta,
        estat_proces="pendent" # Inicialment no hi ha vídeo ni anàlisi
    )
    
    db.add(nova_entrevista)
    db.commit()
    db.refresh(nova_entrevista)
    return nova_entrevista

@app.get("/entrevistas/me", response_model=List[EntrevistaResponse], tags=["Entrevistes"])
def list_my_interviews(
    db: Session = Depends(get_db),
    usuari_actual: Usuari = Depends(get_current_user)
):
    """Retorna l'historial d'entrevistes de l'usuari que ha fet login."""
    return db.query(Entrevista).filter(Entrevista.id_usuari == usuari_actual.id).all()

@app.get("/entrevistas/{id}", response_model=EntrevistaResponse, tags=["Entrevistes"])
def get_interview_detail(
    id: int, 
    db: Session = Depends(get_db),
    usuari_actual: Usuari = Depends(get_current_user)
):
    """Retorna els detalls (estat, mètriques, etc.) d'una entrevista concreta."""
    entrevista = db.query(Entrevista).filter(Entrevista.id == id).first()
    
    if not entrevista:
        raise HTTPException(status_code=404, detail="Entrevista no trobada")
        
    if entrevista.id_usuari != usuari_actual.id:
        raise HTTPException(status_code=403, detail="No tens permís per veure aquesta entrevista")
        
    return entrevista

@app.get("/entrevistas/{id}/informe", tags=["Entrevistes"])
def get_interview_report(
    id: int, 
    db: Session = Depends(get_db),
    usuari_actual: Usuari = Depends(get_current_user)
):
    """Retorna les dades processades i estructurades per generar gràfiques al frontend."""
    entrevista = db.query(Entrevista).filter(Entrevista.id == id).first()
    
    if not entrevista:
        raise HTTPException(status_code=404, detail="Entrevista no trobada")
        
    if entrevista.id_usuari != usuari_actual.id:
        raise HTTPException(status_code=403, detail="No tens permís per veure aquest informe")

    return {
        "id_entrevista": entrevista.id,
        "estat_proces": entrevista.estat_proces,
        "metriques": entrevista.metriques
    }

@app.get("/usuarios/{id}/entrevistas", response_model=List[EntrevistaResponse], tags=["Entrevistes"])
def list_user_interviews(
    id: int, 
    db: Session = Depends(get_db),
    usuari_actual: Usuari = Depends(get_current_user)
):
    """Llista l'historial de totes les entrevistes gravades per un usuari concret."""
    # Seguretat: només pot veure el seu propi historial
    if usuari_actual.id != id:
        raise HTTPException(status_code=403, detail="No pots veure les entrevistes d'un altre usuari")
        
    entrevistes = db.query(Entrevista).filter(Entrevista.id_usuari == id).all()
    return entrevistes

# ==========================================
# 🎥 ENDPOINT PESAT D'ANÀLISI DE VÍDEO
# ==========================================

@app.post("/analyze", tags=["Anàlisi"])
async def analyze(
    video: UploadFile = File(..., description="Video file of the interview answer"),
    question: str = Form(..., description="The interviewer's question text"),
    language: str = Form("ca", description="Language hint for transcription"),
    id_entrevista: int = Form(..., description="L'ID de l'entrevista pendent"), # NOU: Demanem l'ID
    db: Session = Depends(get_db), # NOU: Ens connectem a la BD
    usuari_actual: Usuari = Depends(get_current_user),
):
    """
    Analitza el vídeo del candidat, extreu-ne les mètriques i les guarda a la base de dades.
    """
    
    # 1. Busquem l'entrevista a la BD i comprovem que sigui del nostre usuari
    entrevista = db.query(Entrevista).filter(Entrevista.id == id_entrevista).first()
    if not entrevista:
        raise HTTPException(status_code=404, detail="Entrevista no trobada")
    if entrevista.id_usuari != usuari_actual.id:
        raise HTTPException(status_code=403, detail="No tens permís per modificar aquesta entrevista")

    # 2. Avisem a la BD que comencem a processar (per si el front-end pregunta l'estat)
    entrevista.estat_proces = "processant"
    db.commit()

    tmp_path = None
    try:
        # Guardem el vídeo temporalment
        suffix = os.path.splitext(video.filename or ".mp4")[1].lower()
        if suffix not in ALLOWED_VIDEO_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Format de vídeo no suportat")
        
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name
            total = 0
            while chunk := await video.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="L'arxiu és massa gran")
                tmp.write(chunk)

        # 3. Executem TOTA la teva IA de cop en un fil separat (per no bloquejar l'API)
        result = await asyncio.to_thread(analyze_interview, tmp_path, question, language)

        # 4. EXCEŀLENT: Guardem els resultats a la BD i posem l'estat en completat
        entrevista.metriques = result
        entrevista.estat_proces = "completat"
        db.commit()

        return JSONResponse(content={
            "message": "Anàlisi completat correctament",
            "id_entrevista": entrevista.id,
            "estat": entrevista.estat_proces
        })

    except HTTPException:
        # Si hi ha hagut un error controlat (ex: arxiu massa gran), no toquem la BD
        raise
    except Exception as e:
        # Si la IA peta, posem l'estat a error perquè l'usuari no es quedi esperant eternament
        logger.error("Analysis endpoint error: %s", e)
        entrevista.estat_proces = "error"
        db.commit()
        raise HTTPException(status_code=500, detail="L'anàlisi del vídeo ha fallat.")

    finally:
        # 5. Esborrem el vídeo pesat per no omplir el disc dur del servidor
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

# ==========================================
# GENERADOR PDF
# ==========================================


@app.get("/test-pdf", tags=["Proves"])
async def test_pdf():
    # 1. Preparem les dades mock directament a l'API
    dades_mock = {
        "nom_usuari": "Alba Suri",
        "data": "25 d'Abril, 2026",
        "pregunta": "Quines diferències hi ha entre una arquitectura monolítica i una de microserveis?",
        "score": 85,
        "feedback_ia": "Has demostrat un gran domini tècnic. La teva explicació sobre el desacoblament de serveis ha estat brillant, tot i que podries millorar el contacte visual durant la meitat de la resposta.",
        "wpm": 130,
        "confiança": 92,
        "emocio": "Positiva / Empatia"
    } 
    
    # 2. Les enviem al teu fitxer pdf_generator
    ruta_pdf = generar_pdf_entrevista(dades_mock)
    
    # 3. Retornem l'arxiu perquè el puguis descarregar
    return FileResponse(
        ruta_pdf, 
        filename="informe_mock.pdf", 
        media_type='application/pdf'
    )

# ==========================================
# ENDPOINTS DE PROVA
# ==========================================

# @app.get("/test-db")
# def test_db_connection(db: Session = Depends(get_db), _user: Usuari = Depends(get_current_user)):
#     try:
#         # Fem una consulta SQL purament de prova
#         result = db.execute(text("SELECT 1")).scalar()
#         if result == 1:
#             return {"status": "Connexió a PostgreSQL perfecta! 🎉"}
#     except Exception as e:
#         return {"status": "Error connectant a la BD", "detall": str(e)}

@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}