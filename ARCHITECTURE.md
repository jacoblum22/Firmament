# Firmament System Architecture

## High-Level Architecture Overview

```mermaid
graph TB
    %% Client Layer
    subgraph "Client Layer"
        UI[React Frontend<br/>TypeScript + Vite]
        Mobile[Mobile Browser<br/>Responsive Design]
    end

    %% API Gateway / Load Balancer
    LB[Load Balancer<br/>NGINX/Cloudflare]

    %% Application Layer
    subgraph "Application Layer"
        API[FastAPI Backend<br/>Python 3.12+]
        Auth[JWT Authentication<br/>Google OAuth]
        Middleware[Security Middleware<br/>CORS + Rate Limiting]
    end

    %% Processing Layer
    subgraph "AI/ML Processing Layer"
        Whisper[Whisper ASR<br/>Audio Transcription]
        PyMuPDF[PyMuPDF<br/>PDF Text Extraction]
        NLTK[NLTK<br/>Text Processing]
        BERTopic[BERTopic<br/>Topic Modeling]
        Embeddings[Sentence Transformers<br/>Text Embeddings]
        OpenAI[OpenAI API<br/>Content Enhancement]
    end

    %% Data Layer
    subgraph "Data Storage Layer"
        Redis[(Redis Cache<br/>Session + Processing)]
        S3[(AWS S3<br/>File Storage)]
        LocalFS[(Local Storage<br/>Temporary Files)]
        Memory[(In-Memory<br/>Processing State)]
    end

    %% External Services
    subgraph "External Services"
        GoogleOAuth[Google OAuth 2.0<br/>Authentication]
        OpenAIAPI[OpenAI API<br/>GPT Enhancement]
        AWS[AWS Services<br/>S3 Storage]
    end

    %% Connections
    UI --> LB
    Mobile --> LB
    LB --> API
    API --> Auth
    API --> Middleware
    
    API --> Whisper
    API --> PyMuPDF
    API --> NLTK
    API --> BERTopic
    API --> Embeddings
    API --> OpenAI
    
    API --> Redis
    API --> S3
    API --> LocalFS
    API --> Memory
    
    Auth --> GoogleOAuth
    OpenAI --> OpenAIAPI
    S3 --> AWS

    %% Styling
    classDef clientLayer fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef appLayer fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef mlLayer fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef dataLayer fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef externalLayer fill:#fce4ec,stroke:#880e4f,stroke-width:2px

    class UI,Mobile clientLayer
    class API,Auth,Middleware appLayer
    class Whisper,PyMuPDF,NLTK,BERTopic,Embeddings,OpenAI mlLayer
    class Redis,S3,LocalFS,Memory dataLayer
    class GoogleOAuth,OpenAIAPI,AWS externalLayer
```

## Detailed Component Architecture

### Frontend Architecture (React + TypeScript)

```mermaid
graph LR
    subgraph "React Frontend"
        App[App.tsx<br/>Main Application]
        
        subgraph "Components"
            Auth[AuthHeader<br/>User Authentication]
            Upload[File Upload<br/>Drag & Drop]
            Progress[Progress Display<br/>Real-time Updates]
            Topics[Topic Display<br/>Interactive Expansion]
            Error[Error Display<br/>User-friendly Messages]
        end
        
        subgraph "Services"
            API[API Service<br/>HTTP Client]
            AuthSvc[Auth Service<br/>Google OAuth]
            Network[Network Utils<br/>Connection Handling]
        end
        
        subgraph "State Management"
            Context[Auth Context<br/>User State]
            Hooks[Custom Hooks<br/>Network Status]
            Local[Local State<br/>Component State]
        end
        
        subgraph "External Libraries"
            Motion[Framer Motion<br/>Animations]
            Tilt[Vanilla Tilt<br/>3D Effects]
            Markdown[React Markdown<br/>Content Rendering]
        end
    end

    App --> Components
    App --> Services
    App --> State Management
    Components --> External Libraries
    Services --> API
```

### Backend Architecture (FastAPI + Python)

```mermaid
graph TB
    subgraph "FastAPI Backend"
        Main[main.py<br/>Application Entry]
        Routes[routes.py<br/>API Endpoints]
        Config[config.py<br/>Environment Management]
        Middleware[middleware.py<br/>Security & CORS]
        
        subgraph "Utilities"
            FileValidator[file_validator.py<br/>Upload Validation]
            ContentCache[content_cache.py<br/>SHA256 Caching]
            Segmentation[semantic_segmentation.py<br/>Text Chunking]
            BERTProcessor[bertopic_processor.py<br/>Topic Modeling]
            ErrorMessages[error_messages.py<br/>User-friendly Errors]
        end
        
        subgraph "Models"
            DataModels[Pydantic Models<br/>Request/Response]
            TypeHints[Type Definitions<br/>Static Typing]
        end
        
        subgraph "Background Tasks"
            FileProcessing[File Processing<br/>Async Tasks]
            ProgressTracking[Progress Tracking<br/>Job Status]
        end
    end

    Main --> Routes
    Routes --> Config
    Routes --> Middleware
    Routes --> Utilities
    Routes --> Models
    Routes --> Background Tasks
```

## Data Flow Architecture

### File Processing Pipeline

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant P as Processing
    participant S as Storage
    participant C as Cache

    U->>F: Upload File
    F->>A: POST /upload-file
    A->>C: Check content hash
    alt File cached
        C->>A: Return cached result
        A->>F: Immediate response
    else New file
        A->>S: Store file
        A->>P: Start processing
        A->>F: Job ID + SSE stream
        
        loop Processing stages
            P->>P: Extract/Transcribe
            P->>P: Segment text
            P->>P: Generate topics
            P->>A: Update progress
            A->>F: SSE progress update
            F->>U: Real-time progress
        end
        
        P->>S: Store results
        P->>C: Cache processed data
        A->>F: Completion + data
    end
    
    F->>U: Display results
```

### Topic Enhancement Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant ML as ML Models
    participant O as OpenAI
    participant C as Cache

    U->>F: Click expand bullet
    F->>A: POST /expand-bullet-point
    A->>C: Check expansion cache
    
    alt Cached expansion
        C->>A: Return cached data
    else Generate new
        A->>ML: Analyze context chunks
        ML->>A: Relevant segments
        A->>O: Generate expansion
        O->>A: Enhanced bullet points
        A->>C: Cache expansion
    end
    
    A->>F: Expansion data
    F->>U: Display nested bullets
```

## Security Architecture

```mermaid
graph TB
    subgraph "Security Layers"
        subgraph "Frontend Security"
            HTTPS[HTTPS Only<br/>TLS Encryption]
            CSP[Content Security Policy<br/>XSS Protection]
            CSRF[CSRF Protection<br/>Token Validation]
        end
        
        subgraph "API Security"
            CORS[CORS Configuration<br/>Origin Validation]
            RateLimit[Rate Limiting<br/>Request Throttling]
            JWT[JWT Tokens<br/>Stateless Auth]
            Validation[Input Validation<br/>File Type Checking]
        end
        
        subgraph "Data Security"
            Encryption[At-rest Encryption<br/>S3 + Local Files]
            TempFiles[Secure Temp Files<br/>Auto-cleanup]
            Hashing[Content Hashing<br/>SHA256 Integrity]
        end
        
        subgraph "Infrastructure Security"
            Network[Network Security<br/>VPC + Firewalls]
            Access[Access Controls<br/>IAM Policies]
            Monitoring[Security Monitoring<br/>Audit Logs]
        end
    end

    HTTPS --> JWT
    JWT --> Validation
    Validation --> Encryption
    RateLimit --> TempFiles
    CSP --> CORS
```

## Deployment Architecture

### Development Environment

```mermaid
graph LR
    subgraph "Local Development"
        Dev[Developer Machine]
        
        subgraph "Frontend Dev"
            Vite[Vite Dev Server<br/>localhost:5173]
            HMR[Hot Module Reload<br/>Instant Updates]
        end
        
        subgraph "Backend Dev"
            Uvicorn[Uvicorn Server<br/>localhost:8000]
            Reload[Auto-reload<br/>Code Changes]
        end
        
        subgraph "Services"
            LocalRedis[Local Redis<br/>Cache Testing]
            LocalFiles[Local Storage<br/>Development Files]
        end
    end

    Dev --> Frontend Dev
    Dev --> Backend Dev
    Backend Dev --> Services
```

### Production Environment Options

```mermaid
graph TB
    subgraph "Production Deployment Options"
        subgraph "Cloud Platforms"
            Railway[Railway<br/>Full Stack Deploy]
            Render[Render<br/>Web Services]
            Vercel[Vercel<br/>Frontend Only]
            Heroku[Heroku<br/>App Platform]
        end
        
        subgraph "Container Deployment"
            Docker[Docker Containers<br/>Isolated Environment]
            Compose[Docker Compose<br/>Multi-service]
            K8s[Kubernetes<br/>Orchestrated Scale]
        end
        
        subgraph "Traditional Hosting"
            VPS[VPS Hosting<br/>Full Control]
            Shared[Shared Hosting<br/>Budget Option]
        end
    end

    subgraph "External Services"
        S3Storage[AWS S3<br/>File Storage]
        RedisCloud[Redis Cloud<br/>Managed Cache]
        GoogleAuth[Google OAuth<br/>Authentication]
        OpenAIService[OpenAI API<br/>AI Enhancement]
    end

    Cloud Platforms --> External Services
    Container Deployment --> External Services
    Traditional Hosting --> External Services
```

## Technology Stack Details

### Core Technologies

| Layer | Technology | Purpose | Version |
|-------|------------|---------|---------|
| **Frontend** | React | UI Framework | 18.x |
| | TypeScript | Type Safety | 5+ |
| | Vite | Build Tool | 6+ |
| | Framer Motion | Animations | Latest |
| **Backend** | FastAPI | Web Framework | 0.100+ |
| | Python | Core Language | 3.12+ |
| | Uvicorn | ASGI Server | Latest |
| | Pydantic | Data Validation | 2+ |
| **AI/ML** | Whisper | Speech Recognition | Latest |
| | BERTopic | Topic Modeling | Latest |
| | Transformers | NLP Models | Latest |
| | NLTK | Text Processing | 3.8+ |
| **Storage** | AWS S3 | File Storage | SDK v3 |
| | Redis | Cache/Sessions | 7+ |
| | Local FS | Temp Storage | - |
| **Security** | JWT | Authentication | Latest |
| | Google OAuth | SSO | 2.0 |
| | CORS | Cross-Origin | Built-in |

### Development Tools

| Category | Tool | Purpose |
|----------|------|---------|
| **Code Quality** | ESLint | JavaScript Linting |
| | Prettier | Code Formatting |
| | Pylint | Python Linting |
| | mypy | Type Checking |
| **Testing** | pytest | Python Testing |
| | Jest | JavaScript Testing |
| **Build** | Docker | Containerization |
| | GitHub Actions | CI/CD Pipeline |

## Performance Characteristics

### Processing Performance

```mermaid
graph LR
    subgraph "File Processing Times"
        PDF[PDF Processing<br/>~1-2 sec/MB]
        Audio[Audio Transcription<br/>~0.3x real-time]
        Text[Text Processing<br/>~0.1 sec/1000 words]
    end
    
    subgraph "ML Processing Times"
        Topics[Topic Generation<br/>~2-5 sec/1000 words]
        Expansion[Bullet Expansion<br/>~1-3 seconds]
        Embedding[Text Embedding<br/>~0.1 sec/sentence]
    end
    
    subgraph "System Performance"
        Memory[Memory Usage<br/>~500MB-2GB peak]
        Storage[Storage Efficiency<br/>Content-based caching]
        Network[Network Optimization<br/>Progressive loading]
    end
```

### Scalability Considerations

- **Horizontal Scaling**: Stateless API design enables multiple instances
- **Caching Strategy**: Content-based SHA256 caching prevents reprocessing
- **Background Processing**: Async task handling for long operations
- **Resource Management**: Configurable memory limits and cleanup
- **Database Sharding**: Topic data can be distributed across instances

This architecture provides a robust, scalable foundation for AI-powered document analysis and study material generation.
