from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .database import Base



class Usuari(Base):
    __tablename__ = "usuaris"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    data_creacio = Column(DateTime, server_default=func.now())
    url_foto = Column(String(500), nullable=True)

    entrevistes = relationship("Entrevista", back_populates="usuari")


class Categoria(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    descripcio = Column(Text, nullable=True)

    # Relació bidireccional amb Preguntes
    preguntes = relationship("Pregunta", back_populates="categoria")


class Pregunta(Base):
    __tablename__ = "preguntes"

    id = Column(Integer, primary_key=True, index=True)
    id_categoria = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"))
    text_pregunta = Column(Text, nullable=False)

    categoria = relationship("Categoria", back_populates="preguntes")
    entrevistes = relationship("Entrevista", back_populates="pregunta")


class Entrevista(Base):
    __tablename__ = "entrevistes"

    id = Column(Integer, primary_key=True, index=True)
    id_usuari = Column(Integer, ForeignKey("usuaris.id", ondelete="CASCADE"), nullable=False, index=True)
    id_pregunta = Column(Integer, ForeignKey("preguntes.id", ondelete="SET NULL"))
    data_hora = Column(DateTime, server_default=func.now())
    url_video = Column(String(500), nullable=True)
    url_informe_pdf = Column(String(500), nullable=True)
    estat_proces = Column(String(50), default="pendent", index=True)
    metriques = Column(JSONB, nullable=True)

    usuari = relationship("Usuari", back_populates="entrevistes")
    pregunta = relationship("Pregunta", back_populates="entrevistes")