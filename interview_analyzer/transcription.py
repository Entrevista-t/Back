"""
Speech-to-text transcription module.

Primary: Groq cloud API (whisper-large-v3) via the official Groq SDK.
Fallback: Local faster-whisper on CPU when Groq is unavailable.
"""

import logging
import os
import re
import threading

from groq import (
    Groq,
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
    APIStatusError,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-loaded local model (thread-safe singleton)
# ---------------------------------------------------------------------------
_local_model = None
_local_model_lock = threading.Lock()


def _get_local_model(model_size: str = "medium"):
    """Return a cached faster-whisper WhisperModel instance."""
    global _local_model
    if _local_model is None:
        with _local_model_lock:
            if _local_model is None:
                from faster_whisper import WhisperModel

                logger.info("Loading local faster-whisper '%s' model (CPU/int8)…", model_size)
                _local_model = WhisperModel(
                    model_size,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=4,
                )
    return _local_model


# ---------------------------------------------------------------------------
# Groq cloud transcription
# ---------------------------------------------------------------------------
def _transcribe_groq(audio_path: str, language: str) -> str:
    """Transcribe via Groq cloud API. Raises on any API/network error."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")

    client = Groq()

    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), audio_file.read()),
            model="whisper-large-v3",
            language=language,
            temperature=0,
            response_format="verbose_json",
        )

    text = transcription.text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


# ---------------------------------------------------------------------------
# Local faster-whisper fallback
# ---------------------------------------------------------------------------
def _transcribe_local(audio_path: str, language: str, model_size: str) -> str:
    """Transcribe using local faster-whisper model on CPU."""
    model = _get_local_model(model_size)
    segments, _info = model.transcribe(audio_path, language=language)

    parts = [segment.text.strip() for segment in segments if segment.text.strip()]
    text = " ".join(parts)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def transcribe(audio_path: str, language: str = "ca", model_size: str = "medium") -> str:
    """
    Transcribe an audio file to clean text.

    Tries the Groq cloud API first; falls back to local faster-whisper on
    failure.  The ``model_size`` parameter is used only for the local fallback.

    Args:
        audio_path: Path to the audio file (WAV recommended).
        language: Language hint (default: Catalan).
        model_size: Local fallback model size (default: 'medium').

    Returns:
        Clean transcription text in the requested language.
    """
    # --- Attempt 1: Groq cloud ---
    try:
        text = _transcribe_groq(audio_path, language)
        logger.info(
            "Transcription via Groq completed: %d characters", len(text),
        )
        return text
    except ValueError:
        # Missing API key — go straight to fallback without logging a warning
        logger.info("GROQ_API_KEY not set; using local transcription directly")
    except (RateLimitError, APIConnectionError, APITimeoutError, APIStatusError) as exc:
        logger.warning("Groq transcription failed (%s); falling back to local model", exc)

    # --- Attempt 2: local faster-whisper ---
    text = _transcribe_local(audio_path, language, model_size)
    logger.info(
        "Transcription via local faster-whisper completed: %d characters", len(text),
    )
    return text
