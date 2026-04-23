"""
LLM feedback generator.

Produces a natural-language summary of interview performance by sending
the transcript, question, and computed metrics to a large language model.
Currently returns a placeholder string while the integration is being
developed.
"""

import logging

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


# TODO: Replace placeholder with actual LLM API call (e.g., OpenAI, Groq, Anthropic)
def generate_feedback(
    transcript: str,
    question: str,
    metrics: dict,
    language: str = "ca",
) -> str:
    """Generate natural-language feedback for an interview answer.

    Args:
        transcript: The transcribed text of the candidate's answer.
        question: The original interview question that was asked.
        metrics: A dict containing computed audio and text metrics that
            provide quantitative context for the feedback.
        language: Target language code for the feedback (default ``"ca"``
            for Catalan).

    Returns:
        A feedback string summarising the candidate's performance.
        Currently returns a placeholder; will be replaced by an LLM call.
    """
    try:
        logger.info(
            "generate_feedback called (language=%s, transcript_len=%d)",
            language,
            len(transcript) if transcript else 0,
        )

        # TODO: Replace placeholder with actual LLM API call (e.g., OpenAI, Groq, Anthropic)
        feedback = _PLACEHOLDER_FEEDBACK

        logger.info("generate_feedback returning placeholder feedback")
        return feedback

    except Exception as e:
        logger.error("Failed to generate LLM feedback: %s", e)
        return _FALLBACK_FEEDBACK
