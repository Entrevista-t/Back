import tempfile
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader

def generar_pdf_entrevista(dades: dict) -> str:
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('informe.html')
    
    # 🪄 Càlcul clau: Convertim WPM a un percentatge per a la barra visual
    wpm = dades.get("wpm", 0)
    # Considerem 160 WPM com el 100% de la barra
    dades["wpm_percent"] = min(100, int((wpm / 160) * 100))
    
    html_out = template.render(dades)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        ruta_pdf = tmp_file.name
        
    HTML(string=html_out).write_pdf(ruta_pdf)
    
    return ruta_pdf