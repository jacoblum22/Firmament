# GitHub Copilot Instructions for StudyMate-v2

## Project Overview
StudyMate-v2 is an AI-powered note generator that processes long-form lectures (audio/PDF/text) into structured topics and study materials using FastAPI backend + React frontend.

## Architecture & Data Flow

### Processing Pipeline (backend/routes.py)
1. **File Upload** → Content validation (backend/utils/file_validator.py)
2. **Content-based Caching** → SHA256 hash checking (backend/utils/content_cache.py)
3. **Transcription/Extraction** → Audio (Whisper), PDF (PyMuPDF), Text
4. **Semantic Segmentation** → Text chunking (backend/utils/semantic_segmentation.py)
5. **BERTopic Processing** → Topic modeling (backend/utils/bertopic_processor.py)
6. **Topic Enhancement** → Cluster expansion + bullet points

### Key Design Patterns

**Lazy Imports**: Routes use fallback functions for optional dependencies
```python
def get_bertopic_processor():
    try:
        from utils.bertopic_processor import process_with_bertopic
        return process_with_bertopic
    except ImportError:
        return fallback_function
```

**Content-based Caching**: Files identified by SHA256 hash, not filename
```python
content_hash = cache.calculate_content_hash(file_bytes)
cached_processed = cache.get_processed_cache(file_bytes)
```

**Background Processing**: Long tasks use FastAPI BackgroundTasks with job status tracking
```python
def set_status(job_id: str, **kwargs):
    JOB_STATUS[job_id] = {**old_status, **kwargs}
```

## Configuration & Environment

**Settings Pattern**: Environment-based config (backend/config.py)
```python
# Uses .env.development or .env.production
settings = Settings()
settings.is_production  # Determines security features
```

**Development vs Production**:
- Dev: Permissive CORS, debug mode, auto-reload
- Prod: Strict CORS, security headers, rate limiting, trusted hosts

## Frontend Integration

**API Communication**: React app calls FastAPI endpoints
- File upload with progress tracking via Server-Sent Events
- Structured topic data returned as TopicResponse interface
- Environment-specific API base URLs in frontend/my-study-mate/src/config.ts

## Testing Philosophy

**Structured Testing** (backend/tests/):
- `config/` - Configuration and environment tests
- `integration/` - API route integration tests  
- `unit/` - Pure function unit tests
- `utils/` - Processing pipeline component tests

Run tests: `pytest backend/tests/`

## Development Workflow

**Backend Setup**:
```bash
cd backend
pip install -r requirements.txt
python setup_nltk_data.py  # Required for NLP features
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Setup**:
```bash
cd frontend/my-study-mate  
npm install
npm run dev  # Runs on port 5173
```

**Key Commands**:
- `python deploy.py --start` - Production deployment
- `python cleanup_files.py` - Clean processed files
- `python security_audit.py` - Security checks

## Critical Files to Understand

- **backend/routes.py**: Main API endpoints and processing logic
- **backend/config.py**: Environment configuration system
- **backend/utils/content_cache.py**: Content-based caching implementation
- **backend/utils/bertopic_processor.py**: Core topic modeling
- **frontend/my-study-mate/src/services/**: API client logic

## Common Patterns When Adding Features

1. **New Processing Step**: Add to backend/utils/, import lazily in routes.py
2. **New API Endpoint**: Add to routes.py with proper error handling via ErrorMessages
3. **Frontend Integration**: Update services/ for API calls, add TypeScript interfaces
4. **Caching**: Use content_cache.py for expensive operations
5. **Configuration**: Add to config.py with environment-specific defaults

## Error Handling
Use `ErrorMessages.get_user_friendly_error()` for consistent error responses with user-friendly messages and detailed logging context.

## Collaboration and Problem-Solving

**Interactive Questions**: When working on this project, always ask questions or seek clarification using `interactive-mcp`. This ensures alignment with project goals and avoids assumptions.

**Sequential Thinking**: Use `sequential-thinking` to break down complex problems into manageable steps. This approach helps maintain clarity and ensures thorough analysis.
