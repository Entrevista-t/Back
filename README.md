<div align="center">
  <img src="assets/images/logo_entrevistat.png" alt="Entrevista't logo" width="200" height="auto" />
  <h1>Entrevista't — Backend</h1>

  <p>
    Plataforma de preparació d'entrevistes amb IA · FastAPI + AI/ML pipeline
  </p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12" />
    <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI" />
    <img src="https://img.shields.io/badge/PostgreSQL-336791?logo=postgresql&logoColor=white" alt="PostgreSQL" />
    <img src="https://img.shields.io/badge/Docker-ready-2496ED?logo=docker" alt="Docker" />
    <img src="https://img.shields.io/badge/Groq-Whisper_v3-F55036" alt="Groq Whisper" />
    <img src="https://img.shields.io/badge/API_Language-Català-FFCD00" alt="Catalan" />
  </p>

  <h4>
    <a href="https://github.com/Entrevista-t/Back/issues/">Report Bug</a>
    <span> · </span>
    <a href="https://github.com/Entrevista-t/Back/issues/">Request Feature</a>
    <span> · </span>
    <a href="https://github.com/Entrevista-t/Back/pulls">Contribute</a>
  </h4>
</div>

<br />

---

## Table of Contents

- [Disclaimer](#disclaimer)
- [About the Project](#about-the-project)
  - [Analysis Pipeline](#analysis-pipeline)
  - [Key Features](#key-features)
- [Architecture](#architecture)
  - [API Endpoints](#api-endpoints)
  - [Database Schema](#database-schema)
  - [Analysis Modules](#analysis-modules)
- [Tech Stack](#tech-stack)
- [Requirements](#requirements)
- [Getting Started](#getting-started)
  - [Docker (Recommended)](#docker-recommended)
  - [Local Python](#local-python)
- [Available Commands](#available-commands)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [CI/CD](#cicd)
- [Contributing](#contributing)
- [License](#license)

---

## Disclaimer

This project is under active development as part of an academic initiative. Features and APIs may change without notice. The frontend (Flutter web & mobile) lives in a [separate repository](https://github.com/Entrevista-t/Front) and consumes this API.

---

## About the Project

**Entrevista't** is an AI-powered interview practice platform. This backend receives video recordings from the Flutter frontend, runs a multi-modal AI analysis pipeline (audio DSP, Whisper transcription, spaCy/SentenceTransformer NLP, DeepFace emotion detection, Gemini LLM feedback), and returns structured metrics. Data is persisted in PostgreSQL via SQLAlchemy.

API tags and docstrings are written in **Catalan (Català)**. Code, comments, and documentation are in English.

### Analysis Pipeline

```mermaid
flowchart TD
    A[📹 Video Upload] --> B[🎵 Audio Extraction<br/>ffmpeg]
    B --> C[🗣️ Transcription<br/>Groq cloud / faster-whisper]
    B --> D[🎵 Audio DSP<br/>librosa]
    A --> E[😊 Emotion Detection<br/>DeepFace + MediaPipe]
    C --> F[📝 NLP Metrics<br/>spaCy + SentenceTransformers]
    C --> G[🤖 LLM Feedback<br/>Gemini 2.5 Flash]
    D --> H[📊 Unified JSON Response]
    E --> H
    F --> H
    G --> H
    H --> I[🗄️ PostgreSQL<br/>JSONB storage]
```

#### `/analyze` Request Lifecycle

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant FF as ffmpeg
    participant W as Whisper
    participant NLP as spaCy + ST
    participant V as DeepFace
    participant LLM as Gemini
    participant DB as PostgreSQL

    C->>API: POST /analyze (video + question + id_pregunta/id_entrevista)
    API->>DB: Store video metadata + status processant
    API-->>C: 202 Accepted (id_entrevista)
    API->>FF: Extract audio in background
    FF-->>API: audio.wav
    API->>W: Transcribe audio
    W-->>API: transcript
    par Parallel Analysis
        API->>NLP: Analyze text (7 metrics)
        API->>V: Analyze video (emotions)
        API->>LLM: Generate feedback
    end
    NLP-->>API: text_metrics
    V-->>API: video_metrics
    LLM-->>API: feedback + score
    API->>DB: Store metrics (JSONB)
    API->>DB: Mark completat or error
```

### Key Features

- 🎙️ **Speech-to-text** — Two-tier transcription: Groq cloud API (whisper-large-v3) as primary, local faster-whisper (medium, CPU/int8) as fallback. Catalan-optimised
- 📝 **7 NLP metrics** — question alignment, coherence, information density, specificity, lexical richness, confidence index, communication rhythm (WPM)
- 🎵 **Audio analysis** — active speech time, pause detection, phonation ratio via librosa
- 😊 **Emotion detection** — frame-by-frame DeepFace analysis with MediaPipe face mesh, calibrated baselines
- 🤖 **LLM feedback** — Gemini 2.5 Flash generates personalized interview coaching feedback in Catalan
- 🔐 **JWT authentication** — bcrypt password hashing, token-based auth (24 h expiry)
- 🗄️ **PostgreSQL** — SQLAlchemy ORM with JSONB metrics storage
- 📧 **Email notifications** — interview results delivered via Resend
- 🐳 **Two-layer Docker** — heavy ML base image (rarely rebuilt) + lightweight API image (fast iterations)
- 🚀 **CI/CD** — GitHub Actions pipeline with conditional ML base rebuild and Docker Swarm deployment
- 🔒 **Full CRUD** — complete REST endpoints for users, categories, questions, and interviews with role-based access control

---

## Architecture

### API Endpoints

#### 🔐 Authentication

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | Public | Create a new account |
| POST | `/auth/login` | Public | Authenticate and receive JWT token |

#### 👤 Users (Usuaris)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/usuarios/me` | 🔒 JWT | Get current user's profile |
| POST | `/usuarios` | 🔒 JWT | Create a user (internal) |
| GET | `/usuarios` | 🔒 JWT | List all users |
| GET | `/usuarios/{id}` | 🔒 JWT | Get user by ID |
| PUT | `/usuarios/{id}` | 🔒 Owner | Full update (nom, email, password) |
| PATCH | `/usuarios/{id}` | 🔒 Owner | Partial update |
| DELETE | `/usuarios/{id}` | 🔒 Owner | Delete user |

#### 🏷️ Categories (Categories)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/categorias` | Public | List all categories |
| POST | `/categorias` | 🔒 JWT | Create a category |
| PUT | `/categorias/{id}` | 🔒 JWT | Full update |
| PATCH | `/categorias/{id}` | 🔒 JWT | Partial update |
| DELETE | `/categorias/{id}` | 🔒 JWT | Delete category |

#### ❓ Questions (Preguntes)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/preguntas` | Public | List questions (optional `?categoria_id=` filter) |
| GET | `/preguntas/random?categoria_id=` | Public | Random question from a category |
| POST | `/preguntas` | 🔒 JWT | Create a question |
| PUT | `/preguntas/{id}` | 🔒 JWT | Full update |
| PATCH | `/preguntas/{id}` | 🔒 JWT | Partial update |
| DELETE | `/preguntas/{id}` | 🔒 JWT | Delete question |

#### 🎥 Interviews (Entrevistes)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/entrevistas` | 🔒 JWT | Create interview record (status: `pendent`) |
| GET | `/entrevistas/me` | 🔒 JWT | List current user's interviews |
| GET | `/entrevistas/{id}` | 🔒 Owner | Get interview details + metrics |
| GET | `/entrevistas/{id}/informe` | 🔒 Owner | Get structured report data for charts |
| GET | `/usuarios/{id}/entrevistas` | 🔒 Owner | List a user's interview history |

#### 🧠 Analysis

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/analyze` | 🔒 JWT | Upload video, mark interview as processing, queue AI analysis |

> **`/analyze`** accepts `multipart/form-data` with fields: `video` (file), `question` (text), `language` (default: `ca`), and either `id_pregunta` (create-on-upload) or `id_entrevista` (existing pending interview). It returns `202 Accepted` after the video is stored and the interview is marked `processant`; full analysis continues in the background. Max upload: 500 MB. Allowed formats: `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`, `.m4v`, `.wmv`.

#### ⚙️ System

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | Public | Health check |
| GET | `/` | Public | Redirect to Swagger UI (`/docs`) |

### Database Schema

```mermaid
erDiagram
    USUARIS {
        int id PK
        string nom
        string email
        string password
        datetime data_creacio
    }
    CATEGORIES {
        int id PK
        string nom
        string descripcio
    }
    PREGUNTES {
        int id PK
        int id_categoria FK
        string text_pregunta
    }
    ENTREVISTES {
        int id PK
        int id_usuari FK
        int id_pregunta FK
        datetime data_hora
        string url_video
        string url_informe_pdf
        string estat_proces
        json metriques
    }
    USUARIS ||--o{ ENTREVISTES : "has many"
    CATEGORIES ||--o{ PREGUNTES : "contains"
    PREGUNTES ||--o{ ENTREVISTES : "asked in"
```

**Interview states** (`estat_proces`): `pendent` → `processant` → `completat` | `error`

### Analysis Modules

| Module | Purpose | Key Output |
|--------|---------|------------|
| `audio.py` | ffmpeg extraction + librosa DSP | `duration_total`, `active_speech_time`, `phonation_ratio` |
| `transcription.py` | Groq cloud (whisper-large-v3) with local faster-whisper fallback | Clean transcript string (Catalan) |
| `text.py` | spaCy + SentenceTransformer (7 metrics) | `question_alignment`, `discourse_coherence`, `information_density`, `specificity_index`, `lexical_richness`, `confidence_index`, `communication_rhythm_wpm` |
| `video.py` | MediaPipe FaceMesh + DeepFace | `emotion_distribution`, `dominant_emotion`, `emotional_stability` |
| `llm.py` | Gemini 2.5 Flash feedback generation | `feedback` (natural-language), `answer_quality_score` (0.0–1.0) |
| `pipeline.py` | Orchestrator — wires all modules | Unified JSON response |

#### Transcription Strategy

```
transcribe(audio_path)
  ├─ Try: Groq API (whisper-large-v3, language="ca", temperature=0)
  │       Fast (~2-5s), high quality, requires GROQ_API_KEY
  │
  └─ Fallback: faster-whisper local (medium, CPU/int8, 4 threads)
               Slower (~30-60s on i5), no API key needed
               Model pre-downloaded in Docker image
```

#### Pipeline Return Value

`analyze_interview()` returns a unified JSON object:

```json
{
  "transcript": "...",
  "audio_metrics": {
    "duration_total": 45.2,
    "active_speech_time": 38.1,
    "confidence_index": 0.78,
    "communication_rhythm_wpm": 142
  },
  "text_metrics": {
    "question_alignment": 0.85,
    "discourse_coherence": 0.72,
    "information_density": 0.68,
    "specificity_index": 0.74,
    "lexical_richness": 0.61
  },
  "video_metrics": { "..." },
  "feedback": "Natural-language feedback in Catalan",
  "answer_quality_score": 0.85
}
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| API Framework | FastAPI 0.115.6 |
| ASGI Server | Uvicorn 0.34.0 (uvloop) |
| Database | PostgreSQL + SQLAlchemy 2.0 |
| Auth | JWT (PyJWT) + bcrypt (passlib) |
| Transcription | Groq cloud API (whisper-large-v3) + faster-whisper (local fallback) |
| Audio DSP | librosa + ffmpeg |
| NLP | spaCy 3.8 (`ca_core_news_md`) + SentenceTransformers |
| Vision | MediaPipe FaceMesh + DeepFace |
| LLM Feedback | Google Gemini 2.5 Flash (google-generativeai SDK) |
| Email | Resend |
| Validation | Pydantic 2.10 |
| Containerisation | Docker (two-layer: ML base + app) |
| CI/CD | GitHub Actions → Docker Swarm |
| Registry | GitHub Container Registry (ghcr.io) |

---

## Requirements

- **Docker** (recommended) — Docker Desktop or Docker Engine
- **Or** Python 3.12+ with pip
- A running **PostgreSQL** instance
- A `.env` file (see [Configuration](#configuration))

---

## Getting Started

### Docker (Recommended)

1. **Clone the repository:**

```bash
git clone https://github.com/Entrevista-t/Back.git
cd Back
```

2. **Create a `.env` file** (copy from example):

```bash
cp .env.example .env
# Edit .env with your values
```

3. **Use the interactive launcher:**

```powershell
./start.ps1        # Windows
./start.sh         # Linux / macOS
```

This opens a menu with all common tasks. Choose **option 1** to start the dev server with hot reload at `http://localhost:8000`.

Or start manually:

```bash
docker compose -f infra/docker-compose-dev.yml up -d --build
```

4. **Open the API docs** at `http://localhost:8000/docs` (Swagger UI).

### Local Python

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

> Note: ML models (faster-whisper, spaCy, DeepFace) will be downloaded on first request if not cached.

---

## Available Commands

All commands can be run via `./start.ps1` (or `./start.sh`) or directly:

| Task | Command |
|------|---------|
| **Dev server** (hot reload) | `docker compose -f infra/docker-compose-dev.yml up -d --build` |
| **View logs** | `docker compose -f infra/docker-compose-dev.yml logs -f api` |
| **Container terminal** | `docker compose -f infra/docker-compose-dev.yml exec api /bin/bash` |
| **Run tests** | `docker compose -f infra/docker-compose-dev.yml run --rm api pytest` |
| **Debug mode** | `docker compose -f infra/docker-compose.debug.yml up -d --build` |
| **Build ML base image** | `docker build -t ghcr.io/entrevista-t/back:ml-base -f infra/Dockerfile.ml-base .` |
| **Stop containers** | `docker compose -f infra/docker-compose-dev.yml down` |

### `start.ps1` / `start.sh` Menu

| # | Option |
|---|--------|
| 1 | Start/Update environment (Normal mode) |
| 2 | Start/Update environment (Debug mode with debugpy) |
| 3 | View live Output (Logs) |
| 4 | Enter container terminal (Bash) |
| 5 | Run Unit Tests (pytest) |
| 6 | Stop containers |
| 7 | Build & Push ML base image (GHCR) |
| 8 | Stop everything and Exit script |

---

## Project Structure

```
Back/
├── main.py                        # FastAPI app, all route definitions
├── request.py                     # Test script for /analyze endpoint
├── db/
│   ├── database.py                # SQLAlchemy engine, session, get_db()
│   ├── models.py                  # ORM models (Usuari, Categoria, Pregunta, Entrevista)
│   └── schemas.py                 # Pydantic schemas (validation & serialisation)
├── interview_analyzer/            # AI analysis package
│   ├── __init__.py                # Exports analyze_interview()
│   ├── pipeline.py                # Orchestrator — wires all modules
│   ├── audio.py                   # ffmpeg extraction + librosa DSP metrics
│   ├── transcription.py           # Groq cloud + faster-whisper local fallback
│   ├── text.py                    # spaCy + SentenceTransformer NLP (7 metrics)
│   ├── video.py                   # MediaPipe FaceMesh + DeepFace emotions
│   └── llm.py                     # Gemini 2.5 Flash feedback generation
├── infra/                         # Docker & orchestration
│   ├── Dockerfile                 # Multi-stage: runtime & dev targets
│   ├── Dockerfile.ml-base         # Heavy ML dependencies base image
│   ├── docker-compose.yml         # Production compose
│   ├── docker-compose-dev.yml     # Development with hot reload
│   └── docker-compose.debug.yml   # Debug mode with debugpy (port 5678)
├── pdf_generator.py               # WeasyPrint PDF report generation
├── email_service.py               # Resend email notifications
├── templates/                     # Jinja2 HTML templates for PDF reports
├── requirements.txt               # Meta-file (includes all below)
├── requirements-api.txt           # API framework, auth, DB, email
├── requirements-audio-nlp.txt     # Groq, faster-whisper, spaCy, NLP
├── requirements-vision.txt        # OpenCV, MediaPipe, DeepFace
├── requirements-dev.txt           # Dev tools (pytest, debugpy)
├── start.ps1                      # Interactive PowerShell launcher
├── start.sh                       # Interactive Bash launcher
├── .env.example                   # Environment variable template
└── .github/
    └── workflows/
        └── deploy-prod.yml        # CI/CD pipeline (build → push → deploy)
```

### Docker Image Layers

```
┌────────────────────────────────────────┐
│  App Image (runtime or dev)            │  ← requirements-api.txt (fast rebuild)
├────────────────────────────────────────┤
│  ML Base Image (ghcr.io/.../ml-base)   │  ← audio-nlp + vision deps (rarely rebuilt)
│  Pre-downloaded models:                │     faster-whisper medium, spaCy ca_core_news_md
├────────────────────────────────────────┤
│  python:3.12-slim + ffmpeg             │
└────────────────────────────────────────┘
```

Adding API dependencies (FastAPI, auth libs, etc.) only rebuilds the top layer. ML dependencies (faster-whisper, spaCy, DeepFace) are baked into the base image and only rebuilt when `requirements-audio-nlp.txt` or `requirements-vision.txt` change.

### Dependency Groups

| File | Contents |
|------|----------|
| `requirements-api.txt` | FastAPI, Uvicorn, SQLAlchemy, psycopg2, PyJWT, passlib, bcrypt, Pydantic, Resend, python-dotenv |
| `requirements-audio-nlp.txt` | Groq SDK, faster-whisper, librosa, numpy, spaCy, SentenceTransformers, scikit-learn, tf-keras |
| `requirements-vision.txt` | OpenCV (headless), MediaPipe, DeepFace |
| `requirements-dev.txt` | pytest, debugpy |

---

## Configuration

| Variable | Required | Purpose |
|----------|----------|---------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string (`postgresql://user:pass@host:5432/db`) |
| `JWT_SECRET_KEY` | ✅ | Secret key for JWT token signing (falls back to insecure default in dev) |
| `GROQ_API_KEY` | ⬡ Optional | Groq API key for cloud transcription. If absent, uses local faster-whisper |
| `GEMINI_API_KEY` | ⬡ Optional | Google Gemini API key for LLM feedback generation. If absent, returns placeholder feedback |

The `.env` file is read by Docker Compose and `python-dotenv`. Copy `.env.example` and fill in your values.

---

## CI/CD

The GitHub Actions workflow (`.github/workflows/deploy-prod.yml`) triggers on pushes to `main`:

| Job | Condition | Action |
|-----|-----------|--------|
| **changes** | Always | Detects if ML base files changed |
| **build-ml-base** | ML deps changed | Rebuilds & pushes ML base image to GHCR |
| **build-app** | Always | Builds app image on top of ML base, pushes to GHCR |
| **deploy** | App built | SSH into production, `docker service update` on Swarm |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the [GNU Affero General Public License v3.0](LICENSE).

You are free to use, modify, and distribute this software under the terms of the AGPL-3.0. Any modified version that is accessible over a network must also be made available under the same license.

See the [LICENSE](LICENSE) file for the full text.
