# Firmament API Documentation

## Overview

Firmament provides a REST API for processing and analyzing study materials using advanced AI/ML techniques. The API handles file uploads, transcription, semantic segmentation, topic modeling, and intelligent content expansion.

## Base URL

```
Local Development: http://localhost:8000
Production: Configured per deployment
```

## Authentication

The API uses JWT tokens for authentication with Google OAuth integration.

```http
Authorization: Bearer <jwt_token>
```

## Core Endpoints

### 1. File Upload & Processing

#### Upload File
```http
POST /upload-file
Content-Type: multipart/form-data

Form Data:
- file: File (PDF, MP3, WAV, TXT, M4A)
```

**Response:**
```json
{
  "job_id": "uuid-string",
  "message": "File uploaded successfully, processing started"
}
```

#### Get Processing Progress
```http
GET /progress/{job_id}
```

**Server-Sent Events Stream:**
```json
// Uploading
{"stage": "uploading"}

// Preprocessing (audio files)
{"stage": "preprocessing"}

// Transcription progress
{
  "stage": "transcribing",
  "current": 1,
  "total": 10
}

// Saving results
{"stage": "saving_output"}

// Completion
{
  "stage": "done",
  "result": {
    "filename": "example.pdf",
    "text": "Full extracted text...",
    "segments": [...],
    "topics": {...}
  }
}

// Error
{
  "stage": "error",
  "error": "Error message"
}
```

### 2. Content Processing

#### Process Text Chunks
```http
POST /process-chunks
Content-Type: application/json

{
  "text": "Full document text",
  "filename": "document.pdf"
}
```

**Response:**
```json
{
  "num_chunks": 25,
  "total_words": 1542,
  "message": "Text processed into semantic chunks"
}
```

#### Generate Topic Headings
```http
POST /generate-headings
Content-Type: application/json

{
  "filename": "document.pdf"
}
```

**Response:**
```json
{
  "topics": {
    "topic_0": {
      "heading": "Introduction to Machine Learning",
      "examples": ["Example text chunks..."],
      "segment_positions": ["0", "1", "5"],
      "bullet_points": null
    }
  },
  "segments": [
    {
      "position": "0",
      "text": "Machine learning is a subset..."
    }
  ],
  "filename": "document.pdf"
}
```

### 3. Topic Enhancement

#### Expand Topic Cluster
```http
POST /expand-cluster
Content-Type: application/json

{
  "filename": "document.pdf",
  "cluster_id": "topic_0"
}
```

**Response:**
```json
{
  "cluster": {
    "bullet_points": [
      "• Key concept 1",
      "• Key concept 2",
      "• Key concept 3"
    ]
  }
}
```

#### Expand Bullet Point
```http
POST /expand-bullet-point
Content-Type: application/json

{
  "bullet_point": "Key concept 1",
  "chunks": ["Relevant text chunks..."],
  "topic_heading": "Introduction to Machine Learning",
  "filename": "document.pdf",
  "topic_id": "topic_0",
  "layer": 1
}
```

**Response:**
```json
{
  "original_bullet": "Key concept 1",
  "expanded_bullets": [
    "• Detailed explanation 1",
    "• Detailed explanation 2",
    "• Supporting evidence"
  ],
  "topic_heading": "Introduction to Machine Learning",
  "chunks_used": 3,
  "layer": 1
}
```

### 4. Authentication

#### Google OAuth Login
```http
POST /auth/google
Content-Type: application/json

{
  "credential": "google_jwt_token"
}
```

**Response:**
```json
{
  "access_token": "jwt_token",
  "user": {
    "email": "user@example.com",
    "name": "User Name",
    "picture": "profile_url"
  }
}
```

#### Token Verification
```http
GET /auth/verify
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "valid": true,
  "user": {
    "email": "user@example.com",
    "name": "User Name"
  }
}
```

### 5. System Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-31T12:00:00Z",
  "services": {
    "database": "connected",
    "redis": "connected",
    "s3": "connected"
  }
}
```

#### Cache Management
```http
POST /admin/cleanup-cache
Authorization: Bearer <admin_jwt_token>

{
  "max_age_hours": 24,
  "dry_run": false
}
```

## Data Models

### FileUpload
```json
{
  "filename": "string",
  "size": "integer",
  "type": "string (pdf|mp3|wav|txt|m4a)",
  "upload_time": "datetime"
}
```

### TopicData
```json
{
  "heading": "string",
  "examples": ["string"],
  "segment_positions": ["string"],
  "bullet_points": ["string"] | null,
  "bullet_expansions": {
    "bullet_key": {
      "original_bullet": "string",
      "expanded_bullets": ["string"],
      "topic_heading": "string",
      "chunks_used": "integer",
      "layer": "integer",
      "sub_expansions": {}
    }
  }
}
```

### Segment
```json
{
  "position": "string",
  "text": "string",
  "start_time": "float | null",
  "end_time": "float | null"
}
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Error title",
  "details": "Detailed error message",
  "user_action": "Suggested user action",
  "error_code": "machine_readable_code",
  "timestamp": "2025-01-31T12:00:00Z"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `file_too_large` | File exceeds 100MB limit |
| `unsupported_format` | File type not supported |
| `processing_failed` | ML processing error |
| `invalid_token` | Authentication failed |
| `rate_limited` | Too many requests |

## Rate Limits

- File uploads: 10 per hour per user
- API requests: 1000 per hour per user
- Bullet point expansions: 50 per hour per user

## Content Processing Pipeline

1. **File Upload** → Content validation and storage
2. **Content Extraction** → PDF parsing or audio transcription  
3. **Semantic Segmentation** → Text chunking using NLP
4. **Topic Modeling** → BERTopic clustering and analysis
5. **Topic Enhancement** → Bullet point generation and expansion

## Supported File Types

| Type | Extensions | Max Size | Processing Method |
|------|------------|----------|-------------------|
| PDF | .pdf | 100MB | PyMuPDF text extraction |
| Audio | .mp3, .wav, .m4a | 100MB | Whisper transcription |
| Text | .txt | 100MB | Direct processing |

## Example Workflows

### Complete Document Processing
```bash
# 1. Upload file
curl -X POST http://localhost:8000/upload-file \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"

# 2. Monitor progress (Server-Sent Events)
curl http://localhost:8000/progress/job-uuid \
  -H "Authorization: Bearer $TOKEN"

# 3. Process chunks (if needed)
curl -X POST http://localhost:8000/process-chunks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "...", "filename": "document.pdf"}'

# 4. Generate topics
curl -X POST http://localhost:8000/generate-headings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename": "document.pdf"}'

# 5. Expand specific topics
curl -X POST http://localhost:8000/expand-cluster \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename": "document.pdf", "cluster_id": "topic_0"}'
```

### Interactive Study Enhancement
```bash
# Expand bullet points for deeper understanding
curl -X POST http://localhost:8000/expand-bullet-point \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bullet_point": "Key concept",
    "chunks": ["..."],
    "topic_heading": "Topic Name",
    "filename": "document.pdf",
    "topic_id": "topic_0",
    "layer": 1
  }'
```

## Performance Characteristics

- **PDF Processing**: ~1-2 seconds per MB
- **Audio Transcription**: ~0.3x real-time (30min audio = 9min processing)
- **Topic Modeling**: ~2-5 seconds per 1000 words
- **Bullet Point Expansion**: ~1-3 seconds per expansion

## Security Features

- JWT token authentication
- File type validation
- Content-based caching (SHA256)
- Rate limiting
- CORS protection
- Input sanitization
- Secure temporary file handling
