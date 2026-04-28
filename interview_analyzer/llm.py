"""
LLM feedback generator.

Produces a natural-language summary of interview performance by sending
the transcript, question, and computed metrics to a large language model.
Currently returns placeholder values while the integration is being
developed.
"""
import os
import json
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Placeholder returned when the LLM is not yet wired up or when an error occurs.
_PLACEHOLDER_FEEDBACK = (
    "[Feedback automàtic] Aquesta funcionalitat està en desenvolupament. "
    "Properament, la intel·ligència artificial analitzarà la teva resposta "
    "i et proporcionarà consells personalitzats sobre com millorar la teva "
    "entrevista, incloent-hi aspectes com la claredat, la rellevància de la "
    "resposta, el to de veu i el llenguatge corporal."
)

_FALLBACK_FEEDBACK = (
    "[Error] No s'ha pogut generar el feedback automàtic. "
    "Si us plau, torna-ho a intentar més tard."
)

# Placeholder answer quality score (0.0–1.0) representing how well the
# answer addresses the interview question.
_PLACEHOLDER_ANSWER_QUALITY = 0.72


# TODO: Replace placeholder with actual LLM API call (e.g., OpenAI, Groq, Anthropic)
def generate_feedback(
    transcript: str,
    question: str,
    metrics: dict,
    language: str = "ca",
) -> dict:
    """Generate natural-language feedback and answer quality score.

    Args:
        transcript: The transcribed text of the candidate's answer.
        question: The original interview question that was asked.
        metrics: A dict containing computed audio and text metrics that
            provide quantitative context for the feedback.
        language: Target language code for the feedback (default ``"ca"``
            for Catalan).

    Returns:
        A dict with two keys:
        - ``"feedback"`` (str): Natural-language summary of performance.
        - ``"answer_quality_score"`` (float): 0.0–1.0 score measuring how
          well the answer addresses the question.
        Currently returns placeholder values; will be replaced by an LLM call.
    """
    try:
        logger.info(
            "generate_feedback called (language=%s, transcript_len=%d)",
            language,
            len(transcript) if transcript else 0,
        )

        # TODO: Replace placeholders with actual LLM API call
        # The LLM should evaluate the transcript against the question and
        # return both a textual feedback string and a 0–1 quality score.
        #feedback = _PLACEHOLDER_FEEDBACK
        #answer_quality_score = _PLACEHOLDER_ANSWER_QUALITY

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not found. Returning fallbacks.")
            return {
                "feedback": "No s'ha configurat la clau GEMINI_API_KEY al servidor.",
                "answer_quality_score": 0.0
            }
        
        genai.configure(api_key=api_key)

        system_prompt = f"""
        Ets un expert en Recursos Humans i un 'coach' d'entrevistes de feina exigent però constructiu.
        La teva tasca és analitzar la resposta d'un candidat a una pregunta d'entrevista.
        
        REGLA D'OR: Has d'avaluar si el candidat ha respost REALMENT a la pregunta o si només ha parlat amb coherència però evadint el tema principal.
        
        Has de retornar ÚNICAMENT un objecte JSON pur amb aquestes dues claus:
        - "answer_quality_score": Un número de 0 a 100 avaluant l'alineació de la resposta amb la pregunta (100 = resposta directa i perfecta, <50 = divaga o no respon a la pregunta).
        - "feedback": Un text de 2 o 3 paràgrafs valorant la resposta. Destaca què ha fet bé (segons la transcripció i les mètriques) i què ha de millorar. Utilitza un to empàtic i professional.

        Respon exclusivament en l'idioma amb codi: '{language}' (ca = Català, es = Castellà, en = Anglès).
        """

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash", # El model més ràpid i eficient
            system_instruction=system_prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.7,
            )
        )

        user_prompt = f"""
        PREGUNTA DE L'ENTREVISTADOR: {question}
        
        TRANSCRIPCIÓ DE LA RESPOSTA: "{transcript}"
        
        MÈTRIQUES TÈCNIQUES (Context d'expressió i emocions):
        {json.dumps(metrics, indent=2)}
        """

        # Afegim un timeout de 15 segons
        response = model.generate_content(
            user_prompt,
            request_options={"timeout": 15.0} 
        )
        result_json = json.loads(response.text)

        score = float(result_json.get("answer_quality_score", 0.0))
        feedback_text = str(result_json.get("feedback", _FALLBACK_FEEDBACK))

        logger.info("Feedback de Gemini generat amb èxit. Score: %s", score)
        
        return {
            "feedback": feedback_text,
            "answer_quality_score": score,
        }

    except Exception as e:
        logger.error("Failed to generate LLM feedback: %s", e)
        return {
            "feedback": _FALLBACK_FEEDBACK,
            "answer_quality_score": 0.0,
        }
