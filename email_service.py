import os
import resend
import logging

logger = logging.getLogger(__name__)

# URL del teu front-end per als botons
FRONTEND_URL = "https://entrevistat.kire.ovh"

def generar_plantilla_html(nom_usuari: str, titol: str, contingut: str, text_boto: str, link_boto: str) -> str:
    """Genera un correu HTML estètic i responsive amb els colors de l'app."""
    return f"""
    <!DOCTYPE html>
    <html lang="ca">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #FAFAFA; color: #484B6A; -webkit-font-smoothing: antialiased;">
        <div style="padding: 40px 20px; background-color: #FAFAFA;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                
                <div style="height: 6px; background: linear-gradient(90deg, #6366F1, #8B5CF6);"></div>
                
                <div style="padding: 40px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #6366F1; font-size: 28px; margin: 0; font-weight: 800; letter-spacing: -0.5px;">Entrevista't</h1>
                    </div>
                    
                    <h2 style="font-size: 20px; color: #484B6A; margin-bottom: 20px;">{titol}</h2>
                    <p style="font-size: 16px; line-height: 1.6; color: #484B6A; margin-bottom: 30px;">
                        {contingut}
                    </p>
                    
                    <div style="text-align: center; margin: 40px 0;">
                        <a href="{link_boto}" style="background-color: #6366F1; color: #ffffff; padding: 14px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block;">
                            {text_boto}
                        </a>
                    </div>
                    
                    <p style="font-size: 16px; line-height: 1.6; color: #484B6A;">
                        Ens veiem a dins,<br>
                        <strong>L'equip d'Entrevista't</strong>
                    </p>
                </div>
                
                <div style="background-color: #F2F2F6; padding: 20px; text-align: center; border-top: 1px solid #E4E5F1;">
                    <p style="font-size: 12px; color: #9394A5; margin: 0; line-height: 1.5;">
                        Aquest correu ha estat generat automàticament per <strong>Entrevista't</strong>.<br>
                        Projecte Universitari &copy; 2026
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

def enviar_correu_benvinguda(email_desti: str, nom_usuari: str):
    """
    Envia un correu de benvinguda estètic quan un usuari es registra.
    """
    resend.api_key = os.getenv("RESEND_API_KEY")
    
    if not resend.api_key:
        logger.error("Error: Falta la RESEND_API_KEY al fitxer .env")
        return

    try:
        contingut_text = f"Hola {nom_usuari},<br><br>Ens fa molta il·lusió donar-te la benvinguda a Entrevista't i acompanyar-te en el teu camí cap a l'èxit professional. A partir d'ara, tens al teu abast un espai segur on practicar, equivocar-te i polir les teves habilitats comunicatives amb l'ajuda de la nostra intel·ligència artificial.<br><br>Grava les teves respostes, rep feedback detallat a l'instant i descobreix tot el teu potencial. Estem aquí per donar-te les eines i la confiança necessàries perquè la teva propera entrevista real sigui un èxit absolut."

        html_final = generar_plantilla_html(
            nom_usuari=nom_usuari,
            titol=f"Hola, {nom_usuari} 👋",
            contingut=contingut_text,
            text_boto="Fer la meva primera entrevista",
            link_boto=f"{FRONTEND_URL}/practicar"
        )

        params = {
            "from": "Entrevista't <no-reply@entrevistat.kire.ovh>",
            "to": [email_desti],
            "subject": "Benvingut/da a Entrevista't! Prepara't per brillar ✨",
            "html": html_final
        }

        resend.Emails.send(params)
        logger.info(f"Correu de benvinguda enviat a {email_desti}")
        
    except Exception as e:
        logger.error(f"Error enviant correu de benvinguda: {e}")


def enviar_informe_per_correu(email_desti: str, nom_usuari: str, ruta_pdf: str):
    """
    Envia el PDF adjunt amb un correu HTML estètic a l'usuari.
    """
    resend.api_key = os.getenv("RESEND_API_KEY")
    
    if not resend.api_key:
        logger.error("Error: Falta la RESEND_API_KEY al fitxer .env")
        return

    try:
        contingut_text = f"Hola {nom_usuari},<br><br>Enhorabona per completar la teva simulació d'entrevista! Adjunt a aquest correu trobaràs el teu informe de rendiment detallat en format PDF.<br><br>A dins hi hem analitzat el contingut de la teva resposta, la teva fluïdesa, la teva seguretat i, fins i tot, la teva estabilitat emocional. Revisa amb calma el feedback de la IA i pren nota dels punts on pots millorar.<br><br>Recorda que la pràctica fa la perfecció: cada nova gravació és una oportunitat d'or per polir el teu discurs i destacar per sobre de la resta."

        html_final = generar_plantilla_html(
            nom_usuari=nom_usuari,
            titol="Bon treball! Aquí tens els teus resultats 🚀",
            contingut=contingut_text,
            text_boto="Tornar a practicar",
            link_boto=f"{FRONTEND_URL}"
        )

        # Llegim el PDF si existeix
        attachments = []
        if os.path.exists(ruta_pdf):
            with open(ruta_pdf, "rb") as f:
                pdf_content = list(f.read())
                attachments.append({
                    "filename": f"Informe_Entrevista_{nom_usuari}.pdf",
                    "content": pdf_content,
                })
        else:
            logger.warning(f"⚠️ El fitxer PDF no s'ha trobat a la ruta: {ruta_pdf}")

        params = {
            "from": "Entrevista't <no-reply@entrevistat.kire.ovh>",
            "to": [email_desti],
            "subject": "📊 El teu informe d'entrevista ja està llest!",
            "html": html_final,
            "attachments": attachments
        }

        resend.Emails.send(params)
        logger.info(f"Informe PDF enviat amb èxit a {email_desti}")
        
    except Exception as e:
        logger.error(f"Error enviant l'informe a {email_desti}: {e}")