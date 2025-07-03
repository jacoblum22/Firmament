# Docker Deployment Guide

## Overview

The StudyMate API includes multiple Docker deployment options to suit different requirements and environments.

## Dockerfile Options

### 1. Standard Dockerfile
**File**: `Dockerfile`
- **Health Check**: Uses `curl` command
- **Dependencies**: Includes curl, gcc, g++, ffmpeg
- **Use Case**: Standard production deployment

### 2. Minimal Dockerfile
**File**: `Dockerfile.minimal`
- **Health Check**: Uses Python-based script
- **Dependencies**: Minimal set without curl
- **Use Case**: Smaller image size, security-conscious deployments

## Health Check Options

### Option 1: curl-based (Standard)
```dockerfile
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

**Pros:**
- ✅ Simple and standard approach
- ✅ Widely used in Docker community
- ✅ Fast execution

**Cons:**
- ❌ Requires installing curl package
- ❌ Slightly larger image size

### Option 2: Python-based (Minimal)
```dockerfile
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python healthcheck.py || exit 1
```

**Pros:**
- ✅ No additional packages required
- ✅ Smaller image size
- ✅ More control over health check logic
- ✅ Can check application-specific health

**Cons:**
- ❌ Slightly slower than curl
- ❌ Additional Python file to maintain

## Build Commands

### Standard Build
```bash
# Build standard image
docker build -t studymate-api:latest .

# Build minimal image
docker build -f Dockerfile.minimal -t studymate-api:minimal .
```

### Multi-stage Build (Advanced)
```bash
# Build for development
docker build --target development -t studymate-api:dev .

# Build for production
docker build --target production -t studymate-api:prod .
```

## Running Containers

### Single Container
```bash
# Standard image
docker run -d \
  --name studymate-api \
  -p 8000:8000 \
  --env-file .env.production \
  studymate-api:latest

# Minimal image
docker run -d \
  --name studymate-api \
  -p 8000:8000 \
  --env-file .env.production \
  studymate-api:minimal
```

### Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f studymate-api

# Stop services
docker-compose down
```

## Health Check Testing

### Manual Health Check
```bash
# Test curl-based health check
docker exec studymate-api curl -f http://localhost:8000/health

# Test Python-based health check
docker exec studymate-api python healthcheck.py

# Check health status
docker inspect --format='{{.State.Health.Status}}' studymate-api
```

### Health Check Logs
```bash
# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' studymate-api
```

## Image Size Comparison

| Image Type | Approximate Size | Health Check | Dependencies |
|------------|------------------|--------------|--------------|
| Standard   | ~800MB          | curl         | Full set     |
| Minimal    | ~750MB          | Python       | Minimal      |

## Production Recommendations

### For High-Traffic Production
- Use **standard Dockerfile** with curl health check
- Enable all monitoring and logging features
- Use external Redis and PostgreSQL

### For Resource-Constrained Environments
- Use **minimal Dockerfile** with Python health check
- Consider multi-stage builds to reduce size further
- Use lightweight alternatives where possible

### For Security-Critical Environments
- Use **minimal Dockerfile** to reduce attack surface
- Regularly update base images
- Use non-root user (already implemented)
- Scan images for vulnerabilities

## Environment Configuration

### Required Environment Variables
```bash
# Core
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql://user:pass@db:5432/studymate

# Redis
REDIS_URL=redis://redis:6379/0

# Security
API_KEY=your-secure-api-key
TRUSTED_HOSTS=your-domain.com
```

### Volume Mounts
```yaml
volumes:
  - ./uploads:/var/uploads
  - ./temp:/var/temp
  - ./logs:/var/log/studymate
```

## Troubleshooting

### Health Check Failures
```bash
# Check if service is running
docker ps
docker logs studymate-api

# Test health endpoint manually
curl http://localhost:8000/health

# Check health check script
docker exec studymate-api python healthcheck.py
```

### Common Issues

1. **Health check failing immediately**
   - Check if port 8000 is exposed
   - Verify application is starting correctly
   - Check start_period in health check

2. **curl: command not found**
   - Use minimal Dockerfile with Python health check
   - Or ensure curl is installed in system dependencies

3. **Permission denied errors**
   - Check file permissions in container
   - Verify appuser has access to required directories

## Performance Optimization

### Build Optimization
```dockerfile
# Use .dockerignore to exclude unnecessary files
# Layer caching: copy requirements first
# Multi-stage builds for smaller production images
```

### Runtime Optimization
```dockerfile
# Use gunicorn for production WSGI server
# Configure worker processes based on CPU cores
# Enable HTTP/2 and gzip compression
```

## Security Best Practices

1. **Non-root user**: ✅ Already implemented
2. **Minimal base image**: ✅ Using slim variant
3. **Security scanning**: Regular vulnerability scans
4. **Secrets management**: Use Docker secrets or external vault
5. **Network security**: Restrict container network access
