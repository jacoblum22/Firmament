# Firmament System Architecture

## High-Level Architecture Overview

```mermaid
graph TB
    subgraph Client_Layer
        UI[React_Frontend]
        Mobile[Mobile_Browser]
    end

    LB[Load_Balancer]

    subgraph Application_Layer
        API[FastAPI_Backend]
        Auth[JWT_Authentication]
        Middleware[Security_Middleware]
    end

    subgraph AI_ML_Processing
        Whisper[Whisper_ASR]
        PyMuPDF[PyMuPDF]
        NLTK[NLTK]
        BERTopic[BERTopic]
        Embeddings[Sentence_Transformers]
        OpenAI[OpenAI_API]
    end

    subgraph Data_Storage
        Redis[(Redis_Cache)]
        S3[(AWS_S3)]
        LocalFS[(Local_Storage)]
        Memory[(In_Memory)]
    end

    subgraph External_Services
        GoogleOAuth[Google_OAuth]
        OpenAIAPI[OpenAI_API]
        AWS[AWS_Services]
    end

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
```

## Detailed Component Architecture

### Frontend Architecture (React + TypeScript)

```mermaid
graph LR
    subgraph React_Frontend
        App[App.tsx]
        
        subgraph Components
            Auth[AuthHeader]
            Upload[File_Upload]
            Progress[Progress_Display]
            Topics[Topic_Display]
            Error[Error_Display]
        end
        
        subgraph Services
            API[API_Service]
            AuthSvc[Auth_Service]
            Network[Network_Utils]
        end
        
        subgraph State_Management
            Context[Auth_Context]
            Hooks[Custom_Hooks]
            Local[Local_State]
        end
        
        subgraph External_Libraries
            Motion[Framer_Motion]
            Tilt[Vanilla_Tilt]
            Markdown[React_Markdown]
        end
    end

    App --> Components
    App --> Services
    App --> State_Management
    Components --> External_Libraries
    Services --> API
```

### Backend Architecture (FastAPI + Python)

```mermaid
graph TB
    subgraph FastAPI_Backend
        Main[main.py]
        Routes[routes.py]
        Config[config.py]
        Middleware[middleware.py]
        
        subgraph Utilities
            FileValidator[file_validator.py]
            ContentCache[content_cache.py]
            Segmentation[semantic_segmentation.py]
            BERTProcessor[bertopic_processor.py]
            ErrorMessages[error_messages.py]
        end
        
        subgraph Models
            DataModels[Pydantic_Models]
            TypeHints[Type_Definitions]
        end
        
        subgraph Background_Tasks
            FileProcessing[File_Processing]
            ProgressTracking[Progress_Tracking]
        end
    end

    Main --> Routes
    Routes --> Config
    Routes --> Middleware
    Routes --> Utilities
    Routes --> Models
    Routes --> Background_Tasks
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
    subgraph Security_Layers
        subgraph Frontend_Security
            HTTPS[HTTPS_Only]
            CSP[Content_Security_Policy]
            CSRF[CSRF_Protection]
        end
        
        subgraph API_Security
            CORS[CORS_Configuration]
            RateLimit[Rate_Limiting]
            JWT[JWT_Tokens]
            Validation[Input_Validation]
        end
        
        subgraph Data_Security
            Encryption[At_rest_Encryption]
            TempFiles[Secure_Temp_Files]
            Hashing[Content_Hashing]
        end
        
        subgraph Infrastructure_Security
            Network[Network_Security]
            Access[Access_Controls]
            Monitoring[Security_Monitoring]
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
    subgraph Local_Development
        Dev[Developer_Machine]
        
        subgraph Frontend_Dev
            Vite[Vite_Dev_Server]
            HMR[Hot_Module_Reload]
        end
        
        subgraph Backend_Dev
            Uvicorn[Uvicorn_Server]
            Reload[Auto_reload]
        end
        
        subgraph Services
            LocalRedis[Local_Redis]
            LocalFiles[Local_Storage]
        end
    end

    Dev --> Frontend_Dev
    Dev --> Backend_Dev
    Backend_Dev --> Services
```

### Production Environment Options

```mermaid
graph TB
    subgraph Production_Deployment
        subgraph Cloud_Platforms
            Railway[Railway]
            Render[Render]
            Vercel[Vercel]
            Heroku[Heroku]
        end
        
        subgraph Container_Deployment
            Docker[Docker_Containers]
            Compose[Docker_Compose]
            K8s[Kubernetes]
        end
        
        subgraph Traditional_Hosting
            VPS[VPS_Hosting]
            Shared[Shared_Hosting]
        end
    end

    subgraph External_Services
        S3Storage[AWS_S3]
        RedisCloud[Redis_Cloud]
        GoogleAuth[Google_OAuth]
        OpenAIService[OpenAI_API]
    end

    Cloud_Platforms --> External_Services
    Container_Deployment --> External_Services
    Traditional_Hosting --> External_Services
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

This architecture provides a robust, scalable foundation for AI-powered document analysis and study material generation.
