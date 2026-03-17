# Dockerfile
FROM python:3.12-slim

# Variables de entorno de Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copiar SOLO el archivo de requerimientos primero para la caché
COPY requirements.txt .

# Instalar las dependencias básicas
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer el puerto estándar de FastAPI
EXPOSE 8000

# Comando de arranque (apuntando a la carpeta app y archivo main.py)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]