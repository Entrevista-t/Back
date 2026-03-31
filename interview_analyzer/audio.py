"""
Audio signal processing module.

Handles audio extraction from video files and DSP-based metrics
(duration, active speech time, pause detection, phonation ratio).
"""

import os
import subprocess
import tempfile
import logging

import librosa
import numpy as np

logger = logging.getLogger(__name__)


def extract_audio_from_video(video_path: str) -> str:
    """
    Extract audio track from a video file into a temporary WAV file.
    Returns the path to the temp WAV (caller must clean up).
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_path = tmp.name
    tmp.close()

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",              # no video
        "-ac", "1",         # mono
        "-ar", "16000",     # 16 kHz
        "-acodec", "pcm_s16le",
        tmp_path,
    ]

    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )

    if result.returncode != 0:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        err = result.stderr.decode(errors="ignore")
        raise RuntimeError(f"ffmpeg audio extraction failed (exit={result.returncode}): {err}")

    return tmp_path


def load_audio_mono_16k(file_path: str, target_sr: int = 16000):
    """
    Load audio robustly:
    1. Try librosa directly.
    2. If it fails, convert via ffmpeg to WAV mono 16 kHz, then retry.
    Returns (y, sr).
    """
    # Direct attempt
    try:
        y, sr = librosa.load(file_path, sr=target_sr, mono=True)
        return y, sr
    except Exception as e:
        logger.warning("librosa.load failed for %s: %s. Trying ffmpeg fallback.", file_path, e)

    # ffmpeg fallback
    temp_wav = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            temp_wav = tmp.name

        cmd = [
            "ffmpeg", "-y",
            "-i", file_path,
            "-ac", "1",
            "-ar", str(target_sr),
            temp_wav,
        ]
        completed = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
        )

        if completed.returncode != 0:
            err = completed.stderr.decode(errors="ignore")
            raise RuntimeError(f"ffmpeg conversion failed (exit={completed.returncode}): {err}")

        y, sr = librosa.load(temp_wav, sr=target_sr, mono=True)
        return y, sr
    finally:
        if temp_wav and os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except OSError:
                pass


def analyze_audio_signal(file_path: str) -> dict:
    """
    Compute DSP-based acoustic metrics from an audio file.

    Returns dict with:
      - duration_total: total audio length in seconds
      - active_speech_time: seconds of non-silent audio
      - pause_time: seconds of silence
      - phonation_ratio: active_speech_time / duration_total
    """
    try:
        y, sr = load_audio_mono_16k(file_path, target_sr=16000)

        if y is None or len(y) == 0:
            raise ValueError("Empty audio signal after loading")

        duration = librosa.get_duration(y=y, sr=sr)
        non_silent = librosa.effects.split(y, top_db=25)
        active_time = sum((end - start) for start, end in non_silent) / sr
        pause_time = duration - active_time
        phonation_ratio = active_time / duration if duration > 0 else 0.0

        return {
            "duration_total": round(float(duration), 2),
            "active_speech_time": round(float(active_time), 2),
            "pause_time": round(float(pause_time), 2),
            "phonation_ratio": round(float(phonation_ratio), 2),
        }

    except Exception as e:
        logger.error("Error analyzing audio signal (%s): %s", file_path, e)
        return {
            "duration_total": 0.0,
            "active_speech_time": 0.0,
            "pause_time": 0.0,
            "phonation_ratio": 0.0,
        }
