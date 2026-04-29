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
            "from": "Entrevista-T <no-reply@entrevistat.kire.ovh>", # El remitent per defecte de Resend (capa gratuïta)
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

def enviar_correu_benvinguda(email_desti: str, nom_usuari: str):
    """
    Envia un correu de benvinguda quan un usuari es registra.
    """
    resend.api_key = os.getenv("RESEND_API_KEY")
    
    try:
        params = {
            "from": "Entrevista-t <no-reply@entrevistat.kire.ovh>",
            "to": [email_desti],
            "subject": f"Benvingut/da a Entrevista't, {nom_usuari}!",
            "html": f"""
                <div style="font-family: sans-serif; color: #333;">
                    <h1 style="color: #7E57C2;">Benvingut/da a Entrevista't!</h1>
                    <p>Hola <strong>{nom_usuari}</strong>,</p>
                    <p>Moltes gràcies per apuntar-te a la nostra plataforma. Estem molt contents de tenir-te amb nosaltres!</p>
                    <p>A partir d'ara, podràs practicar les teves entrevistes de feina, rebre mètriques en temps real i millorar la teva comunicació gràcies a la nostra IA.</p>
                    <p style="margin-top: 20px;"><strong>Endavant amb les entrevistes!</strong></p>
                    <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="font-size: 0.8em; color: #999;">L'equip d'Entrevista't</p>
                </div>
            """
        }

        resend.Emails.send(params)
        logger.info(f"Correu de benvinguda enviat a {email_desti}")
        
    except Exception as e:
        logger.error(f"Error enviant correu de benvinguda: {e}")