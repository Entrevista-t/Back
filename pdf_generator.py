import tempfile
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader

def generar_pdf_entrevista(dades: dict) -> str:
    """
    Genera un document PDF a partir de les dades de l'entrevista
    i retorna la ruta temporal on s'ha guardat.
    """
    # 1. Carregar la plantilla HTML
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('informe.html')
    
    # 2. Injectar les dades (siguin de prova o reals) al HTML
    html_out = template.render(dades)
    
    # 3. Crear un arxiu temporal únic per a aquest PDF
    # delete=False és clau perquè el fitxer sobrevisqui prou temps perquè FastAPI el pugui enviar
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        ruta_pdf = tmp_file.name
        
    # 4. Convertir l'HTML a PDF i guardar-lo a la nova ruta
    HTML(string=html_out).write_pdf(ruta_pdf)
    
    return ruta_pdf