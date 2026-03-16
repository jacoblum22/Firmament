# StudyMate Backend

FastAPI backend for StudyMate v2 with comprehensive CORS configuration and security features.

## Features

- 🔒 **Environment-based CORS configuration**
- 🛡️ **Security headers and middleware**
- 🚀 **Production-ready deployment**
- 📊 **Health check endpoints**
- 🔄 **Rate limiting**
- 🏗️ **Trusted host validation**

## Quick Start

### Development Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup NLTK data (recommended)**
   ```bash
   python setup_nltk_data.py
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env.development
   # Edit .env.development with your settings
   ```

4. **Run development server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Production Deployment

1. **Configure production environment**
   ```bash
   cp .env.example .env.production
   # Edit .env.production with your production settings
   ```

2. **Run deployment script**
   ```bash
   python deploy.py --start
   ```

## Environment Configuration

### Required Variables

- `ENVIRONMENT`: `development` or `production`
- `ALLOWED_ORIGINS`: Comma-separated list of allowed origins

### Optional Variables

- `DEBUG`: Enable/disable debug mode (default: `true` for dev, `false` for prod)
- `ALLOW_CREDENTIALS`: Allow credentials in CORS (default: `true`)
- `API_KEY`: API key for additional security
- `SECURE_HEADERS`: Enable security headers (default: `true` for prod)

### Example Configuration

#### Development (.env.development)
```bash
ENVIRONMENT=development
DEBUG=true
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
ALLOW_CREDENTIALS=true
```

#### Production (.env.production)
```bash
ENVIRONMENT=production
DEBUG=false
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
ALLOW_CREDENTIALS=true
API_KEY=your-secure-api-key
SECURE_HEADERS=true
```

## Security Features

### Development
- Permissive CORS for local development
- Multiple localhost origins supported
- Debug mode enabled for detailed error messages

### Production
- Strict CORS validation
- Security headers (CSP, XSS protection, etc.)
- Rate limiting (100 requests/minute per IP)
- Trusted host validation
- HTTPS enforcement headers

## API Endpoints

### Health Check
- `GET /` - Basic service info
- `GET /health` - Detailed health check

### Application Endpoints
- `POST /upload` - File upload
- `POST /process-chunks` - Process text chunks
- `POST /generate-headings` - Generate topic headings
- `POST /expand-cluster` - Expand topic clusters
- `POST /expand-bullet-point` - Expand bullet points
- `GET /progress/{job_id}` - Job progress (SSE)

## Testing

Run the full test suite from the project root:

```bash
pytest
```

Or from the `backend/` directory:

```bash
python -m pytest tests/
```

See `tests/README.md` for details on test categories and individual test commands.

## Deployment Checklist

### Pre-deployment
- [ ] Update `.env.production` with actual domains
- [ ] Update `TrustedHostMiddleware` allowed hosts in `main.py`
- [ ] Set `ENVIRONMENT=production`
- [ ] Run NLTK data setup: `python setup_nltk_data.py`
- [ ] Test CORS with production frontend
- [ ] Verify security headers
- [ ] Test rate limiting

### Production Setup
- [ ] HTTPS configured
- [ ] Firewall rules configured
- [ ] Monitoring set up
- [ ] Backup strategy in place
- [ ] SSL certificates valid

## Troubleshooting

### Common CORS Issues

1. **"CORS policy" error in browser**
   - Check frontend origin is in `ALLOWED_ORIGINS`
   - Verify environment file is loaded correctly
   - Check browser network tab for preflight requests

2. **404 on preflight OPTIONS request**
   - Ensure FastAPI is handling OPTIONS requests
   - Check middleware order in `main.py`

3. **Rate limiting too aggressive**
   - Adjust limits in `middleware.py`
   - Consider user-based rate limiting
   - Implement request queuing

### Development Issues

1. **Environment not loading**
   - Check file naming (`.env.development` vs `.env`)
   - Verify file permissions
   - Check python-dotenv installation

2. **Import errors**
   - Ensure all dependencies are installed
   - Check Python path and virtual environment
   - Verify file structure

## Contributing

1. Follow existing code style
2. Add tests for new features
3. Update documentation
4. Test in both development and production modes

## License

[Your License Here]

---

## Dependency Management

### Requirements Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Core runtime dependencies (pinned versions) |
| `requirements-dev.txt` | Development extras: testing, linting, formatting |

### Installation

```bash
# Runtime only
pip install -r requirements.txt

# Development setup (includes testing, linting)
pip install -r requirements.txt -r requirements-dev.txt
```

### Management Scripts

**Windows (PowerShell):**
```powershell
.\deps.ps1 install       # Install production deps
.\deps.ps1 install-dev   # Install dev deps
.\deps.ps1 test          # Run full test suite
.\deps.ps1 lint          # Run linter
.\deps.ps1 format        # Auto-format code
```

**Unix/Linux (Make):**
```bash
make install     # Install production deps
make install-dev # Install dev deps
make test        # Run full test suite
```
