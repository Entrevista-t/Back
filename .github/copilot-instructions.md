# Copilot Instructions — Entrevista't (FastAPI Backend)

## Project overview

FastAPI backend for the Entrevista't interview practice platform. Receives video recordings from the Flutter frontend, runs an AI analysis pipeline (audio DSP, Whisper transcription, spaCy/SentenceTransformer NLP, DeepFace emotion detection), and returns structured metrics. Persists data in PostgreSQL via SQLAlchemy. **API tags and docstrings are in Catalan. Code, comments, and docs in English.**

---

## Commands

### Development (Docker)
```powershell
# Interactive launcher — covers all common tasks
./infra/start.ps1

# Start dev server with hot reload
docker-compose -f infra/docker-compose-dev.yml up -d --build
# API runs at http://localhost:8000
# Swagger UI at http://localhost:8000/docs
```

### Local Python (no Docker)
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Tests
```bash
pytest                        # full suite
pytest tests/test_analyze.py  # single file
```

### Environment
Requires a `.env` file (copy from `.env.example`):
```
DATABASE_URL=postgresql://<user>:<password>@<host>/<db>
```

---

## Architecture

```
.
├── main.py                  # FastAPI app, all route definitions
├── database.py              # SQLAlchemy engine, Base, get_db() dependency
├── requirements.txt
├── infra/                   # Docker & orchestration files
│   ├── Dockerfile
│   ├── Dockerfile.ml-base
│   ├── docker-compose.yml
│   ├── docker-compose-dev.yml
│   ├── docker-compose.debug.yml
│   ├── start.ps1
│   └── start.sh
└── interview_analyzer/      # AI analysis package
    ├── __init__.py          # Exports analyze_interview()
    ├── pipeline.py          # Orchestrator — wires all modules together
    ├── audio.py             # ffmpeg extraction + librosa DSP metrics
    ├── transcription.py     # Whisper transcription
    ├── text.py              # spaCy + SentenceTransformer NLP metrics (7 metrics)
    └── video.py             # MediaPipe FaceMesh + DeepFace emotion analysis
```

### Route groups (tags)
| Tag | Prefix | Status |
|---|---|---|
| Autenticació | `/auth` | Stub |
| Usuaris | `/usuarios` | Stub |
| Entrevistes | `/entrevistas` | Stub |
| Preguntes | `/preguntas` | Stub |
| Analyze | `/analyze` | **Implemented** |

> ⚠️ Most CRUD routes are stubs returning mock data. Only `/analyze` (POST) runs the full pipeline.

### Analysis pipeline (`interview_analyzer/pipeline.py`)
`analyze_interview(video_path, question, language)` runs these steps in order:
1. **audio.py** — extract WAV with ffmpeg; compute `duration_total`, `active_speech_time`
2. **transcription.py** — Whisper → transcript string
3. **text.py** — 7 NLP metrics: `question_alignment`, `discourse_coherence`, `information_density`, `specificity_index`, `lexical_richness`, `confidence_index`, `communication_rhythm_wpm`
4. **video.py** — MediaPipe face detection + DeepFace → aggregated emotion breakdown

Returns:
```json
{
  "transcript": "...",
  "audio_metrics": { "duration_total", "active_speech_time", "confidence_index", "communication_rhythm_wpm" },
  "text_metrics":  { "question_alignment", "discourse_coherence", "information_density", "specificity_index", "lexical_richness" },
  "video_metrics": { ... }
}
```

### Database (`database.py`)
- SQLAlchemy `create_engine` + `sessionmaker`; `Base = declarative_base()`
- `get_db()` is a FastAPI dependency (yields a session, closes on exit)
- Schema defined in `database_schema.drawio`: **Usuaris**, **Categories**, **Preguntes**, **Entrevistes** (with `metriques JSON` column)

---

## Code conventions

- **Files**: `snake_case.py` — **Classes**: `PascalCase` — **Private helpers**: `_prefixed`
- Route functions: thin handlers — business logic lives in `interview_analyzer/`
- Each `interview_analyzer` module has a single public function; keep internal helpers private (`_prefixed`)
- Upload size limit: `MAX_UPLOAD_BYTES = 500 MB` (enforced in `/analyze` with chunked read)
- Long-running analysis is offloaded with `asyncio.to_thread()` to avoid blocking the event loop
- Temp files (video, extracted WAV) are always cleaned up in `finally` blocks
- NLP models (`spaCy`, `SentenceTransformer`) are loaded once at module import; log a warning and degrade gracefully if a model is missing
- Filler word patterns (Catalan + Spanish) are compiled once as a module-level regex in `text.py`