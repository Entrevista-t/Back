from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db, engine, Base
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from interview_analyzer import analyze_interview
import os
import asyncio
import tempfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500 MB

app = FastAPI(
    title="Entrevistat't API",
    description="Backend para el proyecto universitario",
    version="1.0.0"
)

@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse(url="/docs")

# ==========================================
# 🔐 AUTENTICACIÓ
# ==========================================

@app.post("/auth/register", tags=["Autenticació"])
def register():
    """Crea un compte nou (Registre)."""
    return {"message": "Usuari registrat correctament"}

@app.post("/auth/login", tags=["Autenticació"])
def login():
    """Autentica l'usuari i retorna un token (Login)."""
    return {"access_token": "fake-jwt-token", "token_type": "bearer"}


# ==========================================
# 👤 USUARIS (CRUD i Perfil)
# ==========================================

# NOTA IMPORTANT: '/usuarios/me' ha d'anar SEMPRE abans que '/usuarios/{id}' 
# perquè FastAPI llegeix de dalt a baix i podria confondre 'me' amb un ID.

@app.get("/usuarios/me", tags=["Usuaris"])
def get_current_user_profile():
    """Retorna les dades del perfil de l'usuari autenticat actualment."""
    return {"id": 1, "nom": "Usuari Actual", "email": "admin@entrevistatt.com"}

@app.post("/usuarios", tags=["Usuaris"])
def create_user():
    """Crea un nou usuari (normalment d'ús intern/admin)."""
    return {"message": "Usuari creat", "id": 2}

@app.get("/usuarios", tags=["Usuaris"])
def list_users():
    """Llista tots els usuaris."""
    return [{"id": 1, "nom": "Usuari 1"}, {"id": 2, "nom": "Usuari 2"}]

@app.get("/usuarios/{id}", tags=["Usuaris"])
def get_user(id: int):
    """Retorna els detalls d'un usuari específic."""
    return {"id": id, "nom": f"Detalls de l'usuari {id}"}

@app.put("/usuarios/{id}", tags=["Usuaris"])
def update_user_full(id: int):
    """Reemplaça totes les dades d'un usuari."""
    return {"message": f"Usuari {id} actualitzat completament"}

@app.patch("/usuarios/{id}", tags=["Usuaris"])
def update_user_partial(id: int):
    """Modifica camps específics d'un usuari."""
    return {"message": f"Usuari {id} modificat parcialment"}

@app.delete("/usuarios/{id}", tags=["Usuaris"])
def delete_user(id: int):
    """Elimina un usuari."""
    return {"message": f"Usuari {id} eliminat"}


# ==========================================
# 🎥 ENTREVISTES / ANÀLISI
# ==========================================

@app.post("/entrevistas", tags=["Entrevistes"])
def upload_interview():
    """Rep l'arxiu de vídeo/àudio. Retorna l'ID de l'entrevista i un estat inicial."""
    return {
        "id_entrevista": 101, 
        # "filename": file.filename, 
        "status": "processant"
    }

@app.get("/entrevistas/{id}", tags=["Entrevistes"])
def get_interview_status(id: int):
    """Retorna els detalls d'una entrevista. Aquí el front comprovarà l'estat i rebrà mètriques crues."""
    return {"id": id, "status": "completat", "metriques": "..."}

@app.get("/entrevistas/{id}/informe", tags=["Entrevistes"])
def get_interview_report(id: int):
    """Retorna les dades processades i estructurades per generar gràfiques al frontend."""
    return {"id": id, "informe": "Dades estructurades per a gràfiques"}

@app.get("/usuarios/{id}/entrevistas", tags=["Entrevistes"])
def list_user_interviews(id: int):
    """Llista l'historial de totes les entrevistes gravades per un usuari concret."""
    return [
        {"id_entrevista": 101, "usuari_id": id, "data": "2024-03-20"},
        {"id_entrevista": 102, "usuari_id": id, "data": "2024-03-21"}
    ]


# ==========================================
# ❓ PREGUNTES
# ==========================================

@app.get("/preguntas", tags=["Preguntes"])
def get_questions(
    # categoria: Optional[str] = Query(None, description="Filtra per categoria (ex: tecnica, personal)"), 
    # random: bool = Query(False, description="Retorna les preguntes en ordre aleatori")
):
    """Retorna una llista de preguntes amb opcions de filtratge via query params."""
    return {
        # "categoria_filtrada": categoria,
        # "aleatori": random,
        "preguntes": [
            "Quines són les teves fortaleses?",
            "Explica'm un repte tècnic que hagis superat."
        ]
    }

@app.get("/test-db")
def test_db_connection(db: Session = Depends(get_db)):
    try:
        # Fem una consulta SQL purament de prova
        result = db.execute(text("SELECT 1")).scalar()
        if result == 1:
            return {"status": "Connexió a PostgreSQL perfecta! 🎉"}
    except Exception as e:
        return {"status": "Error connectant a la BD", "detall": str(e)}
    
@app.post("/analyze")
async def analyze(
    video: UploadFile = File(..., description="Video file of the interview answer"),
    question: str = Form(..., description="The interviewer's question text"),
    language: str = Form("ca", description="Language hint for transcription"),
):
    """
    Analyze a candidate's interview video.

    Accepts a video file and the interviewer's question, then returns
    audio, text, and video metrics evaluating the candidate's performance.
    """
    tmp_path = None
    try:
        # Save uploaded video to a temp file with size limit
        suffix = os.path.splitext(video.filename or ".mp4")[1]
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name
            total = 0
            while chunk := await video.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="File too large")
                tmp.write(chunk)

        # Run the blocking analysis pipeline in a thread to avoid freezing the event loop
        result = await asyncio.to_thread(analyze_interview, tmp_path, question, language)
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Analysis endpoint error: %s", e)
        raise HTTPException(status_code=500, detail="Analysis failed")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}