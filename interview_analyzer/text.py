"""
Text / NLP analysis module.

Computes all linguistic metrics adapted for interview evaluation:
  1. question_alignment — cosine similarity between question and answer embeddings
  2. discourse_coherence — logical thread evaluation (global coherence + topic adherence)
  3. information_density — ratio of content words to total words
  4. specificity_index — ratio of nouns to (nouns + pronouns)
  5. lexical_richness — Type-Token Ratio (unique words / total words)
  6. confidence_index — phonation ratio + filler word count
  7. communication_rhythm_wpm — words per minute
"""

import re
import logging

import numpy as np
import spacy
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# --- Load NLP models ---

try:
    nlp = spacy.load("ca_core_news_md")
except OSError:
    logger.warning("spaCy model 'ca_core_news_md' not found. Using blank Catalan model.")
    nlp = spacy.blank("ca")

try:
    semantic_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
except Exception as e:
    logger.warning("Could not load SentenceTransformer: %s", e)
    semantic_model = None

# Filler patterns (Catalan + Spanish + universal hesitations)
FILLER_PATTERNS = [
    r"\behhh+\b", r"\bemmm+\b", r"\bmmm+\b", r"\buhh+\b",
    r"\bah+\b", r"\beh+\b",
    r"\beste\b", r"\bbueno\b", r"\bpues\b", r"\bo sigui\b",
    r"\ba veure\b", r"\bcom dir\b", r"\bno sé\b",
    r"\bdigamos\b", r"\bosea\b", r"\bo sea\b",
]
_filler_regex = re.compile("|".join(FILLER_PATTERNS), re.IGNORECASE)


# ---------------------------------------------------------------------------
# Segmentation
# ---------------------------------------------------------------------------

def smart_segmentation(text: str, max_words: int = 25) -> list[str]:
    """Split text into semantic segments, avoiding breaking subordinate clauses."""
    if not text:
        return []

    doc = nlp(text)
    base_sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    final_segments = []

    for sent in base_sentences:
        words = sent.split()
        if len(words) <= max_words:
            final_segments.append(sent)
        else:
            sub_segments = re.split(
                r"[,:;]|\s+(?:però|mentre|doncs|tampoc|encara|així|i)\s+",
                sent,
            )
            current_chunk = []
            for sub in sub_segments:
                current_chunk.append(sub)
                if len(" ".join(current_chunk).split()) > 6:
                    final_segments.append(" ".join(current_chunk).strip())
                    current_chunk = []
            if current_chunk:
                final_segments.append(" ".join(current_chunk).strip())

    return [s for s in final_segments if len(s.split()) > 3]


# ---------------------------------------------------------------------------
# Individual metric functions
# ---------------------------------------------------------------------------

def compute_question_alignment(question: str, answer: str) -> float:
    """Cosine similarity between question and answer embeddings (0-1)."""
    if not semantic_model or not question or not answer:
        return 0.0

    embeddings = semantic_model.encode([question, answer])
    sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return round(float(sim), 2)


def compute_discourse_coherence(text: str) -> dict:
    """
    Evaluate logical structure of the candidate's speech.

    Returns:
      - global_coherence: similarity between beginning and end of speech
      - topic_adherence: average similarity of each sentence to the topic centroid
      - sentence_count: number of segments analyzed
    """
    if not semantic_model or not text or not text.strip():
        return {"global_coherence": 0.0, "topic_adherence": 0.0, "sentence_count": 0}

    sentences = smart_segmentation(text, max_words=30)
    if len(sentences) < 2:
        return {"global_coherence": 1.0, "topic_adherence": 1.0, "sentence_count": len(sentences)}

    embeddings = semantic_model.encode(sentences)

    # Global coherence: start vs end
    head_n = min(2, len(embeddings))
    start_vec = np.mean(embeddings[:head_n], axis=0)
    end_vec = np.mean(embeddings[-head_n:], axis=0)
    global_coh = cosine_similarity([start_vec], [end_vec])[0][0]

    # Topic adherence: distance to centroid
    centroid = np.mean(embeddings, axis=0)
    adherence_scores = cosine_similarity(embeddings, [centroid])
    avg_adherence = np.mean(adherence_scores)

    return {
        "global_coherence": round(float(global_coh), 2),
        "topic_adherence": round(float(avg_adherence), 2),
        "sentence_count": len(sentences),
    }


def compute_information_density(doc) -> float:
    """
    Ratio of content words (nouns, verbs, adjectives, adverbs, proper nouns)
    to total words. Higher = more informative speech.
    """
    total = len(doc)
    if total == 0:
        return 0.0

    content_count = sum(
        1 for token in doc
        if token.pos_ in ("NOUN", "VERB", "ADJ", "ADV", "PROPN") and not token.is_stop
    )
    return round(content_count / total, 2)


def compute_specificity_index(doc) -> float:
    """
    Ratio of nouns to (nouns + pronouns). Higher = more specific/concrete speech.
    A candidate who names tools, metrics, and specifics scores higher than one
    who uses vague pronouns ("we did that thing").
    """
    noun_count = sum(1 for t in doc if t.pos_ == "NOUN")
    pronoun_count = sum(1 for t in doc if t.pos_ == "PRON")
    total = noun_count + pronoun_count
    if total == 0:
        return 0.0
    return round(noun_count / total, 2)


def compute_lexical_richness(doc) -> float:
    """
    Type-Token Ratio (TTR): unique word forms / total words.
    Higher = richer vocabulary.
    """
    words = [token.text.lower() for token in doc if token.is_alpha]
    if not words:
        return 0.0
    return round(len(set(words)) / len(words), 2)


def count_fillers(text: str) -> int:
    """Count filler words and hesitation patterns in the transcription."""
    if not text:
        return 0
    return len(_filler_regex.findall(text))


def compute_confidence_index(phonation_ratio: float, filler_count: int, total_words: int) -> float:
    """
    Combined confidence score (0-1). Higher = more confident delivery.

    Based on:
      - phonation_ratio: high ratio = fewer awkward silences
      - filler_ratio: fewer fillers relative to words = more confident
    """
    filler_ratio = filler_count / total_words if total_words > 0 else 0.0
    # Weighted combination: 60% phonation, 40% (1 - filler_ratio)
    score = 0.6 * phonation_ratio + 0.4 * max(0.0, 1.0 - filler_ratio * 10)
    return round(min(1.0, max(0.0, score)), 2)


def compute_wpm(word_count: int, active_speech_seconds: float) -> float:
    """Words per minute based on active speech time (excluding silences)."""
    if active_speech_seconds <= 0:
        return 0.0
    return round(word_count / (active_speech_seconds / 60), 1)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def analyze_text(transcription: str, question: str, audio_signal: dict) -> dict:
    """
    Run all text/NLP metrics on a transcription.

    Args:
        transcription: Full transcription text from Whisper.
        question: The interviewer's question text.
        audio_signal: Dict from audio.analyze_audio_signal() with timing data.

    Returns:
        Dict with all 7 adapted interview metrics.
    """
    doc = nlp(transcription) if transcription else nlp("")
    total_words = len([t for t in doc if t.is_alpha])
    filler_count = count_fillers(transcription)

    phonation_ratio = audio_signal.get("phonation_ratio", 0.0)
    active_speech = audio_signal.get("active_speech_time", 0.0)

    return {
        "question_alignment": compute_question_alignment(question, transcription),
        "discourse_coherence": compute_discourse_coherence(transcription),
        "information_density": compute_information_density(doc),
        "specificity_index": compute_specificity_index(doc),
        "lexical_richness": compute_lexical_richness(doc),
        "confidence_index": {
            "phonation_ratio": phonation_ratio,
            "pause_time": audio_signal.get("pause_time", 0.0),
            "filler_count": filler_count,
            "score": compute_confidence_index(phonation_ratio, filler_count, total_words),
        },
        "communication_rhythm_wpm": compute_wpm(total_words, active_speech),
    }
