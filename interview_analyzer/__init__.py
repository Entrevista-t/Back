"""
interview_analyzer — Unified interview analysis package.

Processes a video file + question text and returns audio, text, and video metrics
adapted for job interview evaluation.
"""

from .pipeline import analyze_interview

__all__ = ["analyze_interview"]
