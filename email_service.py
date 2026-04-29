import os
import resend
import logging

logger = logging.getLogger(__name__)

def enviar_informe_per_correu(email_desti: str, nom_usuari: str, ruta_pdf: str):
    """
    Envia el PDF adjunt per correu electrònic a l'usuari.
    """
    resend.api_key = os.getenv("RESEND_API_KEY")
    
    if not resend.api_key:
        logger.error("Error: Falta la RESEND_API_KEY al fitxer .env")
        return

    try:
        # Llegim el contingut del PDF per adjuntar-lo
        with open(ruta_pdf, "rb") as f:
            pdf_content = list(f.read())

        params = {
            "from": "Entrevista-T <onboarding@resend.dev>", # El remitent per defecte de Resend (capa gratuïta)
            "to": [email_desti],
            "subject": f"El teu informe d'Entrevista't, {nom_usuari}!",
            "html": f"<strong>Hola {nom_usuari}!</strong><br><p>T'adjuntem l'informe de la teva darrera entrevista de pràctica.</p>",
            "attachments": [
                {
                    "filename": "informe_entrevista.pdf",
                    "content": pdf_content,
                }
            ],
        }

        resend.Emails.send(params)
        logger.info(f"Correu enviat correctament a {email_desti}")
        
    except Exception as e:
        logger.error(f"Error enviant correu: {e}")