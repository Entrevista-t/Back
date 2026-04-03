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

**Entrevista't** is an AI-powered interview practice platform. This backend receives video recordings from the Flutter frontend, runs a multi-modal AI analysis pipeline (audio DSP, Whisper transcription, spaCy/SentenceTransformer NLP, DeepFace emotion detection), and returns structured metrics. Data is persisted in PostgreSQL via SQLAlchemy.

API tags and docstrings are written in **Catalan (Català)**. Code, comments, and documentation are in English.

### Analysis Pipeline

```
Video upload → Audio extraction (ffmpeg)
  → Whisper transcription → NLP metrics (7 dimensions)
  → Audio DSP metrics (speech time, pauses, rhythm)
  → Emotion detection (DeepFace + MediaPipe)
    → Unified JSON response
```

### Key Features

- 🎙️ **Speech-to-text** — Whisper transcription with Catalan language support
- 📝 **7 NLP metrics** — question alignment, coherence, information density, specificity, lexical richness, confidence index, communication rhythm (WPM)
- 🎵 **Audio analysis** — active speech time, pause detection, phonation ratio via librosa
- 😊 **Emotion detection** — frame-by-frame DeepFace analysis with MediaPipe face mesh, calibrated baselines
- 🔐 **JWT authentication** — bcrypt password hashing, token-based auth
- 🗄️ **PostgreSQL** — SQLAlchemy ORM with JSONB metrics storage
- 🐳 **Two-layer Docker** — heavy ML base image (rarely rebuilt) + lightweight API image (fast iterations)
- 🚀 **CI/CD** — GitHub Actions pipeline with conditional ML base rebuild and Docker Swarm deployment

---

## Architecture

### API Endpoints

| Method | Path | Tag | Status |
|--------|------|-----|--------|
| POST | `/auth/register` | Autenticació | ✅ Implemented |
| POST | `/auth/login` | Autenticació | ✅ Implemented |
| GET | `/usuarios/me` | Usuaris | ⚠️ Stub |
| POST | `/usuarios` | Usuaris | ⚠️ Stub |
| GET | `/usuarios` | Usuaris | ⚠️ Stub |
| GET | `/usuarios/{id}` | Usuaris | ⚠️ Stub |
| PUT | `/usuarios/{id}` | Usuaris | ⚠️ Stub |
| PATCH | `/usuarios/{id}` | Usuaris | ⚠️ Stub |
| DELETE | `/usuarios/{id}` | Usuaris | ⚠️ Stub |
| POST | `/entrevistas` | Entrevistes | ⚠️ Stub |
| GET | `/entrevistas/{id}` | Entrevistes | ⚠️ Stub |
| GET | `/entrevistas/{id}/informe` | Entrevistes | ⚠️ Stub |
| GET | `/usuarios/{id}/entrevistas` | Entrevistes | ⚠️ Stub |
| GET | `/preguntas` | Preguntes | ⚠️ Stub |
| POST | `/analyze` | — | ✅ Implemented |
| GET | `/test-db` | — | ✅ Implemented |
| GET | `/health` | health | ✅ Implemented |

> ⚠️ Most CRUD routes are stubs returning mock data. The core implemented endpoints are `/auth/*`, `/analyze`, `/health`, and `/test-db`.

### Database Schema

```
Usuari (1) ──→ (N) Entrevista
Categoria (1) ──→ (N) Pregunta
Pregunta (1) ──→ (N) Entrevista
```

| Table | Key Columns |
|-------|-------------|
| `usuaris` | id, nom, email, password (bcrypt), data_creacio |
| `categories` | id, nom, descripcio |
| `preguntes` | id, id_categoria (FK), text_pregunta |
| `entrevistes` | id, id_usuari (FK), id_pregunta (FK), data_hora, url_video, estat_proces, metriques (JSONB) |

### Analysis Modules

| Module | Purpose | Key Output |
|--------|---------|------------|
| `audio.py` | ffmpeg extraction + librosa DSP | `duration_total`, `active_speech_time`, `phonation_ratio` |
| `transcription.py` | OpenAI Whisper (base model) | Transcript string |
| `text.py` | spaCy + SentenceTransformer (7 metrics) | `question_alignment`, `discourse_coherence`, `information_density`, `specificity_index`, `lexical_richness`, `confidence_index`, `communication_rhythm_wpm` |
| `video.py` | MediaPipe FaceMesh + DeepFace | `emotion_distribution`, `dominant_emotion`, `emotional_stability` |
| `pipeline.py` | Orchestrator — wires all modules | Unified JSON response |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| API Framework | FastAPI 0.115.6 |
| ASGI Server | Uvicorn 0.34.0 (uvloop) |
| Database | PostgreSQL + SQLAlchemy 2.0 |
| Auth | JWT (PyJWT) + bcrypt (passlib) |
| Transcription | OpenAI Whisper |
| Audio DSP | librosa + ffmpeg |
| NLP | spaCy 3.8 (`ca_core_news_md`) + SentenceTransformers |
| Vision | MediaPipe FaceMesh + DeepFace |
| Validation | Pydantic 2.10 |
| Containerisation | Docker (two-layer: ML base + app) |
| CI/CD | GitHub Actions → Docker Swarm |
| Registry | GitHub Container Registry (ghcr.io) |

---

## Requirements

- **Docker** (recommended) — Docker Desktop or Docker Engine
- **Or** Python 3.12+ with pip
- A running **PostgreSQL** instance
- A `.env` file with `DATABASE_URL` (see [Configuration](#configuration))

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
# Edit .env with your PostgreSQL connection string
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

> Note: ML models (Whisper, spaCy, DeepFace) will be downloaded on first request.

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
├── database.py                    # SQLAlchemy engine, Base, get_db()
├── db/
│   ├── database.py                # SQLAlchemy engine, session, get_db()
│   ├── models.py                  # ORM models (Usuari, Categoria, Pregunta, Entrevista)
│   └── schemas.py                 # Pydantic schemas (validation & serialisation)
├── interview_analyzer/            # AI analysis package
│   ├── __init__.py                # Exports analyze_interview()
│   ├── pipeline.py                # Orchestrator — wires all modules
│   ├── audio.py                   # ffmpeg extraction + librosa DSP metrics
│   ├── transcription.py           # Whisper transcription
│   ├── text.py                    # spaCy + SentenceTransformer NLP (7 metrics)
│   └── video.py                   # MediaPipe FaceMesh + DeepFace emotions
├── infra/                         # Docker & orchestration
│   ├── Dockerfile                 # Multi-stage: runtime & dev targets
│   ├── Dockerfile.ml-base         # Heavy ML dependencies base image
│   ├── docker-compose.yml         # Production compose
│   ├── docker-compose-dev.yml     # Development with hot reload
│   └── docker-compose.debug.yml   # Debug mode with debugpy (port 5678)
├── requirements.txt               # Meta-file (includes all below)
├── requirements-api.txt           # API framework, auth, DB dependencies
├── requirements-audio-nlp.txt     # Audio processing, Whisper, spaCy, NLP
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
├────────────────────────────────────────┤
│  python:3.12-slim                      │
└────────────────────────────────────────┘
```

Adding API dependencies (FastAPI, auth libs, etc.) only rebuilds the top layer. ML dependencies (Whisper, spaCy, DeepFace) are baked into the base image and only rebuilt when `requirements-audio-nlp.txt` or `requirements-vision.txt` change.

---

## Configuration

| Variable | Where | Purpose |
|----------|-------|---------|
| `DATABASE_URL` | `.env` | PostgreSQL connection string |

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

This project is part of an academic initiative. No formal license has been declared yet. Please contact the maintainers for usage permissions.
