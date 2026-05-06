## 📚 Documentation

- **[📸 Visual Demo & Feature Showcase](./docs/demo.md)** - Interactive screenshots and user journey walkthrough
- **[▶️ Overview video (YouTube)](https://www.youtube.com/watch?v=GwvVlYgfGac)** - End-to-end walkthrough: upload audio, transcribe, chunk, generate topics, expand bullets
- **[🔧 API Documentation](./docs/api.md)** - Complete REST API reference with examples
- **[🏗️ System Architecture](./docs/architecture.md)** - Detailed architecture diagrams and design decisions
- **[⚙️ Configuration Guide](./docs/config.md)** - Environment and deployment configuration
- **[🔒 Security Guide](./docs/security.md)** - Security hardening and audit checklist
- **[🐳 Docker Deployment](./docs/docker.md)** - Container setup and production deployment

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19+-61DAFB.svg)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue.svg)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/License-Custom-lightgrey.svg)](./LICENSE)

---

## 🎯 Overview

Firmament is a sophisticated full-stack application that leverages cutting-edge AI and machine learning to automatically process and analyze long-form content. Built with enterprise-grade architecture, it transforms audio lectures, PDFs, and text documents into intelligently organized topic clusters with actionable insights.

### 📺 Overview video

For a quick look at the full flow in the UI, see the [overview on YouTube](https://www.youtube.com/watch?v=GwvVlYgfGac): uploading an audio file, transcription, chunking, generated topic text, and expanding bullet points.

### 🌟 What Makes Firmament Special

- **🧠 Advanced AI Pipeline**: Integrates OpenAI Whisper, BERTopic, and custom NLP models
- **🔒 Enterprise Security**: OAuth 2.0, JWT authentication, rate limiting, and secure file handling
- **☁️ Cloud-Native**: AWS S3 integration with intelligent caching and content deduplication
- **🎨 Modern Stack**: React 19 + TypeScript frontend with FastAPI + Python backend
- **📊 Real-Time Processing**: Asynchronous job processing with live progress tracking
- **🔄 Production Ready**: Comprehensive testing, environment management, and deployment configurations

---

## ✨ Key Features

### 🎙️ **Intelligent Audio Processing**
- **Multi-Model Transcription**: OpenAI Whisper with model size optimization
- **Audio Enhancement**: RNNoise denoising and preprocessing pipeline
- **Chunk-Based Processing**: Efficient handling of long-form content (90+ minutes)
- **Progress Tracking**: Live job progress via **server-sent events (SSE)** from the API

### 📄 **Document Intelligence**
- **Multi-Format Support**: PDF, audio (MP3/WAV/M4A), and plain text processing
- **Content Extraction**: Advanced PDF parsing with metadata preservation
- **Text Cleaning**: Intelligent preprocessing with NLTK-powered text normalization

### 🧮 **Machine Learning & NLP**
- **Topic Modeling**: BERTopic implementation for semantic clustering
- **Content Segmentation**: Intelligent text chunking with overlap handling
- **Semantic Analysis**: Vector embeddings and similarity detection
- **Automated Summarization**: Cluster-based content organization

### 🔐 **Enterprise-Grade Security**
- **OAuth 2.0 Integration**: Google authentication with JWT token management
- **Rate Limiting**: Redis-backed throttling with graceful fallbacks
- **Content Security**: SHA256 hashing, secure temp files, and input validation
- **CORS & Headers**: Production-ready security middleware

### 🏗️ **Scalable Architecture**
- **Modular monolith**: FastAPI app organized into route modules and utilities; heavy dependencies loaded where needed
- **Content Caching**: Hash-based deduplication with user-specific storage
- **Background Jobs**: FastAPI BackgroundTasks with status tracking
- **Error Handling**: Comprehensive exception management with user-friendly messages

---

## 🛠️ Technology Stack

### **Backend**
- **Framework**: FastAPI (Python 3.11+; tested on 3.11 in CI)
- **AI/ML**: OpenAI Whisper, BERTopic, scikit-learn, NLTK
- **Audio**: pydub, RNNoise, faster-whisper
- **Storage**: AWS S3, Redis (optional)
- **Security**: OAuth 2.0, JWT, rate limiting middleware
- **Testing**: pytest with comprehensive test coverage

### **Frontend**
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite for optimized development and production builds
- **Testing**: Vitest, Testing Library, co-located `*.test.ts(x)` (see `frontend/TESTING.md`)
- **Authentication**: Google OAuth integration with @react-oauth/google
- **State Management**: Context API with JWT token handling
- **Styling**: Modern CSS with responsive design
- **HTTP**: Native `fetch` via `NetworkUtils` (retries, timeouts, auth headers)

### **Infrastructure**
- **Cloud Storage**: AWS S3 with intelligent file organization
- **Authentication**: Google Cloud OAuth 2.0
- **Caching**: Redis for rate limiting and session management
- **Environment Management**: Multi-environment configuration (.env.development, .env.production)
- **Deployment**: Docker-ready with production optimization

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ (3.12 works; tested in CI on 3.11)
- Node.js 18+
- `ffmpeg` on your `PATH` (needed for audio processing)
- An [OpenAI API key](https://platform.openai.com/api-keys) (required for topic generation)
- A [Google OAuth 2.0 Client ID](https://console.cloud.google.com/) (required for sign-in)

### 1. Clone the repository

```bash
git clone https://github.com/jacoblum22/Firmament.git
cd Firmament
```

### 2. Backend setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Install Python dependencies (~5 min first time due to torch/sentence-transformers)
pip install -r requirements.txt

# Download NLTK tokenizer data (one-time)
python docker/setup_nltk_data.py

# Copy the environment template and fill in your keys
cp .env.example .env.development
#  Required values to set in .env.development:
#    OPENAI_API_KEY=sk-...
#    GOOGLE_CLIENT_ID=...  (same value as VITE_GOOGLE_CLIENT_ID in frontend)

# Start the API server (default: http://127.0.0.1:8000)
python start.py
```

> **Windows note:** `start.ps1` is a convenience wrapper that also activates the venv.
> The default port is `8000` (configured via `PORT=` in `.env.development`).
> Change it there if port 8000 is taken on your machine.

### 3. Frontend setup

```bash
cd frontend

# Copy the environment template and fill in your values
cp .env.example .env.local
#  Required values:
#    VITE_API_BASE_URL=http://localhost:8000   (match the backend PORT above)
#    VITE_GOOGLE_CLIENT_ID=<your-google-client-id>

npm install
npm run dev
```

Frontend runs on `http://localhost:5173`.

### 4. Verify everything works

- Open `http://localhost:5173` — you should see a "Backend online" status indicator.
- Sign in with Google and upload a PDF or audio file.
- Topic generation requires a valid `OPENAI_API_KEY`; transcription requires `ffmpeg`.

---

## 🗂️ Project Structure

```
Firmament/
├── backend/
│   ├── app/              FastAPI application (routes, config, middleware)
│   ├── utils/
│   │   ├── audio/        Audio pre-processing and transcription (Whisper)
│   │   ├── nlp/          BERTopic pipeline, cluster headings, text utilities
│   │   ├── security/     Auth, circuit breaker, file validation
│   │   ├── storage/      S3 / local storage, content cache, temp files
│   │   └── common/       Shared OpenAI client, error messages
│   ├── tests/            pytest suite (unit, integration, utils)
│   ├── docker/           Dockerfile, NLTK setup, health check script
│   ├── cache/            ← gitignored; created at runtime (transcriptions, processed)
│   ├── uploads/          ← gitignored; created at runtime
│   ├── models/           ← gitignored; Whisper model cache
│   ├── .env.example      Environment variable template
│   ├── requirements.txt  Python dependencies
│   └── start.py          Launcher script (reads from .env.development / .env.production)
├── frontend/
│   ├── src/
│   │   ├── components/   React components (upload zone, results, auth …)
│   │   ├── hooks/        Custom hooks (upload pipeline, network status, persistence)
│   │   ├── services/     Centralised API calls (apiService.ts)
│   │   └── utils/        Validation, export, network utilities
│   ├── .env.example      Frontend env template (VITE_API_BASE_URL, VITE_GOOGLE_CLIENT_ID)
│   └── TESTING.md        Frontend test layout guide
├── docs/                 API, architecture, security, and deployment docs
└── docker-compose.yml    Production compose file (API + Redis + nginx)
```

---

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-change`).
3. Make your changes and add tests where applicable.
4. Open a pull request describing what changed and why.

For larger changes, please open an issue first to discuss scope and approach.

---

## 📖 Usage Examples

### 1. **Audio Lecture Processing**
```python
# Upload a lecture recording
POST /upload
Content-Type: multipart/form-data

# The system will:
# 1. Apply RNNoise denoising
# 2. Transcribe with Whisper
# 3. Segment into topics with BERTopic
# 4. Generate structured study materials
```

### 2. **PDF Document Analysis**
```python
# Process academic papers or textbooks
POST /upload
Content-Type: multipart/form-data

# Results in:
# - Extracted text with formatting preservation
# - Topic clusters by semantic similarity
# - Key concept identification
# - Searchable content organization
```

### 3. **Real-Time Progress Tracking**
```javascript
// Frontend uses the browser EventSource API (SSE) — see apiService.createProgressEventSource
// and hooks/useUploadPipeline.ts for the live progress stream.

// Typical stage flow from the pipeline:
// 'uploading' → 'processing' → 'transcribing' → 'analyzing' → 'complete'
```

---

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  React Frontend │    │ FastAPI Backend │    │  AI/ML Pipeline │
│                 │    │                 │    │                 │
│ • TypeScript    │◄──►│ • Authentication│◄──►│ • Whisper API   │
│ • OAuth UI      │    │ • File Upload   │    │ • BERTopic      │
│ • Progress      │    │ • Job Queue     │    │ • NLTK/scikit   │
│   Tracking      │    │ • Rate Limiting │    │ • Audio Proc.   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  AWS S3 Storage │    │ Content Caching │    │ Security Layer  │
│                 │    │                 │    │                 │
│ • User Files    │    │ • SHA256 Hash   │    │ • JWT Tokens    │
│ • Processed     │    │ • Deduplication │    │ • CORS Policy   │
│   Content       │    │ • Metadata      │    │ • Rate Limits   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Architectural Patterns

- **🔄 Lazy Loading**: Optional dependencies loaded on-demand
- **📝 Content-Based Caching**: SHA256 hashing prevents duplicate processing
- **⚡ Background Processing**: Non-blocking job execution with status updates
- **🛡️ Security-First**: Multiple layers of authentication and validation
- **📊 Modular Design**: Clean separation of concerns with utility modules

---

## 🐳 Docker Deployment

A production-ready `docker-compose.yml` is provided at the repo root.

### What you need to test Docker locally

1. **Docker Desktop** (or another engine) running.
2. **Production env file** — Compose mounts `backend/.env.production` into the API container:
   ```bash
   cp backend/.env.example backend/.env.production
   ```
   Then edit `backend/.env.production` and set at least:
   - `OPENAI_API_KEY`
   - `JWT_SECRET` (32+ characters; production validation is stricter than dev)
   - `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` if you use Google sign-in through the API
   - **Redis (recommended when using Compose):** uncomment / set  
     `REDIS_URL=redis://:firmament_local_dev_redis@redis:6379/0`  
     so the API can reach the bundled Redis. That password matches the **default** Redis password in `docker-compose.yml` (override with `REDIS_PASSWORD` in a `.env` file next to `docker-compose.yml` for production).
3. **Build and start** (first run downloads large ML wheels inside the image — expect 15–40+ minutes on a cold cache):
   ```bash
   docker compose up --build -d
   ```
4. **Smoke test** — API is published on host port **8000**:
   ```bash
   curl -sS http://localhost:8000/health
   ```
   Nginx is mapped to ports **80** / **443** per `docker-compose.yml` (configure TLS under `backend/ssl/` for HTTPS).

### What runs in CI on every push

The GitHub Actions workflow builds the API image with Docker Buildx and layer caching (`docker-api-image` job). That confirms the **Dockerfile** and **build context** still produce a valid image; it does not start the full Compose stack (that would require your real `.env.production` secrets in CI).

See `docs/docker.md` for full production configuration notes.

> **Do I need to rebuild the Docker image?**
> Yes — if you've changed `requirements.txt` or any Python source files since the last
> image was built, run `docker compose build` before `up`.  A simple `docker compose up`
> won't re-install new dependencies.

---

## 🧪 Testing & Quality Assurance

**Backend (pytest)** — activate your venv first, then from `backend/`:

```bash
cd backend
python -m pytest tests/ -v
```

Tests are discovered automatically from `backend/tests/`.  Three files
(`test_cluster_analysis.py`, `test_s3_connection.py`, `test_s3_production.py`) are standalone
scripts that require live external services; they are excluded from normal pytest collection
via `tests/conftest.py`.

**Frontend (Vitest)** — from the repo root or `frontend/`:

```bash
cd frontend
npm test          # run once
npm run test:coverage
```

See `frontend/TESTING.md` for layout (co-located tests, shared mocks, coverage scope). On GitHub, **CI** runs backend and frontend test jobs on push and pull requests to `main` (`.github/workflows/ci.yml`).

**Backend test categories:**
- Unit tests for utility functions
- Integration tests for API endpoints (using FastAPI `TestClient` — no live server needed)
- Authentication and security tests
- File processing pipeline tests
- NLP / BERTopic processor tests

### Code Quality Features
- **Type Safety**: Full TypeScript coverage on frontend
- **Error Handling**: User-friendly error messages with detailed backend logging
- **Security Auditing**: Automated security checks and file validation

---

## 📄 License

See the [LICENSE](LICENSE) file for licensing terms.

---

## 👥 Author

**Jacob Lum** - *Full-Stack Developer & AI Engineer*
- 🌐 GitHub: [@jacoblum22](https://github.com/jacoblum22)
- 💼 LinkedIn: [Connect with me](https://linkedin.com/in/jacob-lum)

---

<div align="center">

**⭐ If this project demonstrates the kind of work you're looking for, I'd love to discuss opportunities! ⭐**

*Built with passion for intelligent automation and scalable software architecture.*

</div>
