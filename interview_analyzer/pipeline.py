"""
Pipeline orchestrator.

Wires together audio extraction, transcription, text analysis, and video
analysis into a single function call.
"""

import os
import logging

from .audio import extract_audio_from_video, analyze_audio_signal
from .transcription import transcribe
from .text import analyze_text
from .video import analyze_video
from .llm import generate_feedback

logger = logging.getLogger(__name__)


def analyze_interview(video_path: str, question: str, language: str = "ca") -> dict:
    """
    Full interview analysis pipeline.

    Args:
        video_path: Path to the video file.
        question: The interviewer's question text.
        language: Language hint for Whisper transcription (default: Catalan).

    Returns:
        Dict with transcript, audio_metrics, text_metrics, and video_metrics.
    """
    audio_path = None

    try:
        # 1. Extract audio from video
        logger.info("Extracting audio from video...")
        audio_path = extract_audio_from_video(video_path)

        # 2. Transcribe audio → text
        logger.info("Transcribing audio...")
        transcript = transcribe(audio_path, language=language)

        # 3. Analyze audio signal (DSP metrics)
        logger.info("Analyzing audio signal...")
        audio_signal = analyze_audio_signal(audio_path)

        # 4. Analyze text (all 7 NLP metrics)
        logger.info("Analyzing text metrics...")
        text_metrics = analyze_text(transcript, question, audio_signal)

        # 5. Analyze video frames (emotion detection)
        logger.info("Analyzing video emotions...")
        video_metrics = analyze_video(video_path)

        # 6. Generate LLM feedback
        logger.info("Generating LLM feedback...")
        all_metrics = {
            "audio_metrics": {
                "duration_total": audio_signal["duration_total"],
                "active_speech_time": audio_signal["active_speech_time"],
            },
            "text_metrics": dict(text_metrics),  # copy before pop
        }
        llm_result = generate_feedback(
            transcript, question, all_metrics, language=language
        )
        llm_feedback = llm_result["feedback"]
        answer_quality_score = llm_result["answer_quality_score"]

        return {
            "transcript": transcript,
            "audio_metrics": {
                "duration_total": audio_signal["duration_total"],
                "active_speech_time": audio_signal["active_speech_time"],
                "confidence_index": text_metrics.pop("confidence_index"),
                "communication_rhythm_wpm": text_metrics.pop("communication_rhythm_wpm"),
            },
            "text_metrics": text_metrics,
            "video_metrics": video_metrics,
            "llm_feedback": llm_feedback,
            "answer_quality_score": answer_quality_score,
        }

    except Exception as e:
        logger.error("Interview analysis failed: %s", e)
        raise

    finally:
        # Clean up temp audio file
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except OSError:
                pass
