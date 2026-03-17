## 📚 Documentation

- **[📸 Visual Demo & Feature Showcase](./docs/demo.md)** - Interactive screenshots and user journey walkthrough
- **[🔧 API Documentation](./docs/api.md)** - Complete REST API reference with examples
- **[🏗️ System Architecture](./docs/architecture.md)** - Detailed architecture diagrams and design decisions
- **[⚙️ Configuration Guide](./backend/CONFIG_GUIDE.md)** - Environment and deployment configuration
- **[🔒 Security Guide](./docs/security.md)** - Security hardening and audit checklist
- **[🐳 Docker Deployment](./docs/docker.md)** - Container setup and production deployment

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19+-61DAFB.svg)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue.svg)](https://typescriptlang.org)

---

## 🎯 Overview

Firmament is a sophisticated full-stack application that leverages cutting-edge AI and machine learning to automatically process and analyze long-form content. Built with enterprise-grade architecture, it transforms audio lectures, PDFs, and text documents into intelligently organized topic clusters with actionable insights.

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
- **Progress Tracking**: Real-time transcription progress with WebSocket updates

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
- **Microservices Pattern**: Modular utility functions with lazy loading
- **Content Caching**: Hash-based deduplication with user-specific storage
- **Background Jobs**: FastAPI BackgroundTasks with status tracking
- **Error Handling**: Comprehensive exception management with user-friendly messages

---

## 🛠️ Technology Stack

### **Backend**
- **Framework**: FastAPI (Python 3.12+)
- **AI/ML**: OpenAI Whisper, BERTopic, scikit-learn, NLTK
- **Audio**: pydub, RNNoise, faster-whisper
- **Storage**: AWS S3, Redis (optional)
- **Security**: OAuth 2.0, JWT, rate limiting middleware
- **Testing**: pytest with comprehensive test coverage

### **Frontend**
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite for optimized development and production builds
- **Authentication**: Google OAuth integration with @react-oauth/google
- **State Management**: Context API with JWT token handling
- **Styling**: Modern CSS with responsive design
- **HTTP Client**: Axios with authentication interceptors

### **Infrastructure**
- **Cloud Storage**: AWS S3 with intelligent file organization
- **Authentication**: Google Cloud OAuth 2.0
- **Caching**: Redis for rate limiting and session management
- **Environment Management**: Multi-environment configuration (.env.development, .env.production)
- **Deployment**: Docker-ready with production optimization

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
// Frontend WebSocket integration
const [uploadStatus, setUploadStatus] = useState('idle');

// Track processing stages:
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

## 🧪 Testing & Quality Assurance

```bash
# Run comprehensive test suite
cd backend
pytest tests/ -v

# Test categories:
# • Unit tests for utility functions
# • Integration tests for API endpoints
# • Authentication and security tests
# • File processing pipeline tests
# • Error handling and edge cases
```

### Code Quality Features
- **Type Safety**: Full TypeScript coverage on frontend
- **Error Handling**: User-friendly error messages with detailed logging
- **Security Auditing**: Automated security checks and validation

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

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
