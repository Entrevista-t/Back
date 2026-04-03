import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# Leemos la URL. Si por algún motivo no encuentra el .env, lanzará un error para avisarte.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("¡Cuidado! No se ha encontrado DATABASE_URL en el archivo .env")

# Creem el motor de connexió
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Creem la fàbrica de sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe base per als models
Base = declarative_base()

# Dependència per a FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()