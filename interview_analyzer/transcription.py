"""
Speech-to-text transcription module using OpenAI Whisper.
"""

import logging

import whisper

logger = logging.getLogger(__name__)

_models: dict = {}


def _get_model(model_size: str = "base"):
    if model_size not in _models:
        logger.info("Loading Whisper '%s' model...", model_size)
        _models[model_size] = whisper.load_model(model_size)
    return _models[model_size]


def transcribe(audio_path: str, language: str = "ca", model_size: str = "base") -> str:
    """
    Transcribe an audio file to text using Whisper.

    Args:
        audio_path: Path to the audio file (WAV recommended).
        language: Language hint for Whisper (default: Catalan).
        model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large').

    Returns:
        Full transcription text.
    """
    try:
        model = _get_model(model_size)
        result = model.transcribe(audio_path, language=language)
        text = result.get("text", "").strip()
        logger.info("Transcription completed: %d characters", len(text))
        return text
    except Exception as e:
        logger.error("Transcription failed for %s: %s", audio_path, e)
        raise
