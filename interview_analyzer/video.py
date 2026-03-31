"""
Video frame emotion analysis module.

Uses MediaPipe FaceMesh for face detection and DeepFace for emotion
classification. Processes a video file and returns aggregated emotion metrics.
"""

import logging

import cv2
import numpy as np
import mediapipe as mp
from deepface import DeepFace

logger = logging.getLogger(__name__)


class InterviewAnalyzer:
    """
    Core emotion analysis engine. Processes video frames one by one,
    calibrates a baseline, and classifies emotional state relative to it.
    """

    def __init__(self):
        self.FRAME_SKIP = 3
        self.CALIBRATION_FRAMES = 40
        self.DEFAULT_SENSITIVITY = 10.0

        self.LABELS = {
            "angry": "TENSO / MOLESTO", "disgust": "INCOMODO",
            "fear": "NERVIOSO", "happy": "POSITIVO / EMPATIA",
            "sad": "BAJO ANIMO", "surprise": "SORPRENDIDO",
            "neutral": "CALMA / FOCO",
        }

        # Internal state
        self.calibration_data = {k: [] for k in self.LABELS}
        self.baseline_probs = {}
        self.noisy_emotions = []
        self.is_calibrated = False
        self.calibration_step = 0
        self.frame_count = 0

        self.prev_box = None
        self.last_result = None

        # MediaPipe FaceMesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.7,
        )

    def _get_bounding_box(self, face_landmarks, w, h):
        x_vals = [lm.x for lm in face_landmarks.landmark]
        y_vals = [lm.y for lm in face_landmarks.landmark]

        pad = 40
        x1 = max(0, int(min(x_vals) * w) - pad)
        y1 = max(0, int(min(y_vals) * h) - 60)
        x2 = min(w, int(max(x_vals) * w) + pad)
        y2 = min(h, int(max(y_vals) * h) + 40)

        if self.prev_box is None:
            self.prev_box = (x1, y1, x2, y2)
        sx1 = int(x1 * 0.7 + self.prev_box[0] * 0.3)
        sy1 = int(y1 * 0.7 + self.prev_box[1] * 0.3)
        sx2 = int(x2 * 0.7 + self.prev_box[2] * 0.3)
        sy2 = int(y2 * 0.7 + self.prev_box[3] * 0.3)

        self.prev_box = (sx1, sy1, sx2, sy2)
        return (sx1, sy1, sx2, sy2)

    def _apply_logic(self, probs):
        max_diff = -100
        winner = "neutral"

        for emo, score in probs.items():
            base = self.baseline_probs.get(emo, 0)
            diff = score - base
            threshold = 25.0 if emo in self.noisy_emotions else self.DEFAULT_SENSITIVITY
            if diff > threshold and diff > max_diff:
                max_diff = diff
                winner = emo

        if winner in ["fear", "angry", "disgust"] and max_diff < 40:
            winner = "neutral"

        category = "neutral"
        if winner == "happy":
            category = "positive"
        elif winner in ["fear", "angry", "disgust", "sad"]:
            category = "tense"

        return {
            "raw_emotion": winner,
            "category": category,
            "intensity": int(max_diff) if max_diff > 0 else 0,
        }

    def process_frame(self, frame):
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        output = {
            "face_detected": False,
            "is_calibrated": self.is_calibrated,
            "result": None,
        }

        if results.multi_face_landmarks:
            output["face_detected"] = True
            landmarks = results.multi_face_landmarks[0]
            box = self._get_bounding_box(landmarks, w, h)

            should_analyze = (
                self.frame_count % self.FRAME_SKIP == 0
                and (box[2] - box[0]) > 60
            )

            if should_analyze:
                try:
                    face_crop = frame[box[1]:box[3], box[0]:box[2]]
                    obj = DeepFace.analyze(
                        img_path=face_crop, actions=["emotion"],
                        enforce_detection=False, detector_backend="skip", silent=True,
                    )
                    res = obj[0] if isinstance(obj, list) else obj
                    probs = res["emotion"]

                    if not self.is_calibrated:
                        self.calibration_step += 1
                        for emo, val in probs.items():
                            self.calibration_data[emo].append(val)

                        if self.calibration_step >= self.CALIBRATION_FRAMES:
                            for emo in self.calibration_data:
                                avg = np.mean(self.calibration_data[emo])
                                self.baseline_probs[emo] = avg
                                if avg > 30 and emo in ["fear", "angry", "disgust", "sad"]:
                                    self.noisy_emotions.append(emo)
                            self.is_calibrated = True
                    else:
                        self.last_result = self._apply_logic(probs)
                except Exception:
                    pass

            if self.last_result:
                output["result"] = self.last_result

        self.frame_count += 1
        return output

    def close(self):
        self.face_mesh.close()


def analyze_video(video_path: str) -> dict:
    """
    Process all frames of a video file and return aggregated emotion metrics.

    Returns:
      - emotion_distribution: {"positive": %, "neutral": %, "tense": %}
      - dominant_emotion: most frequent category
      - emotional_stability: lower = more stable (std dev of category changes)
    """
    analyzer = InterviewAnalyzer()
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        logger.error("Cannot open video: %s", video_path)
        return _empty_video_result()

    stats = {"positive": 0, "neutral": 0, "tense": 0}
    category_sequence = []

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            data = analyzer.process_frame(frame)

            if data["is_calibrated"] and data["result"]:
                cat = data["result"]["category"]
                stats[cat] += 1
                category_sequence.append(cat)
    finally:
        cap.release()
        analyzer.close()

    total = sum(stats.values())
    if total == 0:
        return _empty_video_result()

    distribution = {k: round(v / total * 100, 1) for k, v in stats.items()}
    dominant = max(stats, key=stats.get)

    # Emotional stability: encode categories as numbers, compute std dev
    cat_to_num = {"positive": 1, "neutral": 0, "tense": -1}
    numeric_seq = [cat_to_num[c] for c in category_sequence]
    stability = round(float(np.std(numeric_seq)), 2) if len(numeric_seq) > 1 else 0.0

    return {
        "emotion_distribution": distribution,
        "dominant_emotion": dominant,
        "emotional_stability": stability,
    }


def _empty_video_result() -> dict:
    return {
        "emotion_distribution": {"positive": 0.0, "neutral": 0.0, "tense": 0.0},
        "dominant_emotion": "neutral",
        "emotional_stability": 0.0,
    }
