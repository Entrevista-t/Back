from fastapi import FastAPI
from fastapi.responses import RedirectResponse

app = FastAPI(
    title="Entrevistat't API",
    description="Backend para el proyecto universitario",
    version="1.0.0"
)

@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse(url="/docs")

@app.get("/api/v1/health", tags=["System"])
def health_check():
    """
    Endpoint de prueba para comprobar que la API de Entrevistat't está viva y respondiendo.
    """
    return {
        "status": "ok", 
        "message": "¡El backend está funcionando a la perfección!"
    }