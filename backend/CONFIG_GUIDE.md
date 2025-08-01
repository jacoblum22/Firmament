# Firmament API Configuration Guide

## Environment-Specific Configuration

The Firmament API supports separate configurations for development and production environments. This ensures optimal settings for each deployment scenario.

## Quick Start

### Development Mode
```bash
# Windows PowerShell
.\start.ps1 development

# Cross-platform Python
python start.py --env development
```

### Production Mode
```bash
# Windows PowerShell
.\start.ps1 production

# Cross-platform Python
python start.py --env production

# Docker
docker-compose up -d
```

## Configuration Files

### Environment Files
- `.env.development` - Development-specific settings
- `.env.production` - Production-specific settings  
- `.env.example` - Template for creating new environment files

### Key Differences

| Setting | Development | Production |
|---------|-------------|------------|
| Debug Mode | `true` | `false` |
| Host | `127.0.0.1` | `0.0.0.0` |
| Auto-reload | `true` | `false` |
| Workers | `1` | `4` |
| CORS Origins | Permissive | Restrictive |
| Rate Limiting | `1000/min` | `100/min` |
| Security Headers | `false` | `true` |
| Log Level | `DEBUG` | `INFO` |
| File Upload Size | `50MB` | `100MB` |
| OpenAI Model | `gpt-3.5-turbo` | `gpt-4` |
| Whisper Model | `base.en` | `large-v2` |

## Configuration Categories

### Server Configuration
- `HOST` - Server host address
- `PORT` - Server port (default: 8000)
- `RELOAD` - Auto-reload on code changes
- `WORKERS` - Number of worker processes

### CORS Configuration
- `ALLOWED_ORIGINS` - Comma-separated list of allowed origins
- `ALLOW_CREDENTIALS` - Allow credentials in CORS requests
- `CORS_MAX_AGE` - Cache duration for preflight requests

### Security Configuration
- `SECURE_HEADERS` - Enable security headers
- `TRUSTED_HOSTS` - Comma-separated list of trusted hosts
- `API_KEY` - API key for authentication
- `RATE_LIMIT_CALLS` - Rate limit: calls per period
- `RATE_LIMIT_PERIOD` - Rate limit: time period in seconds

### Database Configuration
- `DATABASE_URL` - Database connection string
- `DATABASE_POOL_SIZE` - Connection pool size

### File Storage Configuration
- `UPLOAD_MAX_SIZE` - Maximum file upload size in bytes
- `UPLOAD_DIRECTORY` - Directory for uploaded files
- `TEMP_DIRECTORY` - Directory for temporary files

### Logging Configuration
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `LOG_FILE` - Log file path (empty = console only)

### AI Configuration
- `OPENAI_API_KEY` - OpenAI API key
- `OPENAI_MODEL` - OpenAI model to use
- `OPENAI_MAX_TOKENS` - Maximum tokens per request
- `WHISPER_MODEL` - Whisper model for audio transcription
- `AUDIO_CHUNK_DURATION` - Audio chunk duration in seconds

### Performance Configuration
- `MAX_CONCURRENT_REQUESTS` - Maximum concurrent requests

## Environment Setup

### 1. Create Environment File
```bash
# Copy the example file
cp .env.example .env.development

# Edit the file with your settings
nano .env.development
```

### 2. Configure Your Settings
Update the environment file with your specific configuration:

```env
# Example .env.development
ENVIRONMENT=development
DEBUG=true
OPENAI_API_KEY=your-actual-openai-key
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 3. Start the Application
```bash
# Development
python start.py --env development

# Production
python start.py --env production
```

## Production Deployment

### Using Docker
```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f firmament-api

# Stop services
docker-compose down
```

### Manual Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment
export ENVIRONMENT=production

# Start with multiple workers
python start.py --env production --workers 4
```

## Security Best Practices

### Development
- Use placeholder API keys for testing
- Enable debug mode for easier troubleshooting
- Use permissive CORS settings for local development

### Production
- Use strong, unique API keys
- Disable debug mode
- Restrict CORS origins to your actual domains
- Enable security headers and trusted hosts
- Use HTTPS in production
- Set up proper logging and monitoring
- Use environment variables for sensitive data

## Configuration Validation

The application includes a `/config` endpoint that shows current configuration:

```bash
# Development (shows full config)
curl http://localhost:8000/config

# Production (shows limited config)
curl http://localhost:8000/config
```

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Check `ALLOWED_ORIGINS` in your environment file
   - Ensure your frontend URL is included

2. **Rate Limiting**
   - Adjust `RATE_LIMIT_CALLS` and `RATE_LIMIT_PERIOD`
   - Consider different limits for dev/prod

3. **File Upload Issues**
   - Check `UPLOAD_MAX_SIZE` setting
   - Ensure upload directory exists and is writable

4. **Database Connection**
   - Verify `DATABASE_URL` is correct
   - Check database server is running

### Debug Mode

Enable debug mode to get more detailed error messages:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

This will show detailed error information and enable the `/docs` endpoint for API documentation.

## Environment Variables Priority

The configuration system loads environment variables in this order:
1. `.env.{ENVIRONMENT}` (e.g., `.env.development`)
2. `.env` (fallback)
3. System environment variables (highest priority)

This allows you to override specific settings without modifying the environment files.
