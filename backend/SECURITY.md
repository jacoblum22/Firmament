# StudyMate Security Guide

This document outlines the security measures and best practices implemented in StudyMate.

## Table of Contents

1. [Environment Security](#environment-security)
2. [Database Security](#database-security)
3. [API Security](#api-security)
4. [Container Security](#container-security)
5. [Network Security](#network-security)
6. [Monitoring & Auditing](#monitoring--auditing)
7. [Deployment Security](#deployment-security)

## Environment Security

### Environment Variables

All sensitive configuration is managed through environment variables:

```bash
# ❌ NEVER do this (hardcoded secrets)
DATABASE_URL = "postgresql://user:password123@localhost/db"

# ✅ Use environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
```

### Environment Files

- **`.env.development`**: Development settings with safe defaults
- **`.env.production`**: Production settings with secure configurations
- **`.env.example`**: Template with placeholder values

### Secrets Management

1. **Generate secure passwords** using the setup script:
   ```bash
   python setup_production.py
   ```

2. **Store secrets securely**:
   - Use environment variables on production servers
   - Never commit `.env.production` to version control
   - Use password managers for secret storage

3. **Rotate secrets regularly**:
   - Database passwords: Every 90 days
   - API keys: Every 60 days
   - JWT secrets: Every 30 days

## Database Security

### PostgreSQL Configuration

1. **Strong passwords**: Minimum 32 characters with mixed case, numbers, and symbols
2. **Limited access**: Database only accessible from application containers
3. **Encrypted connections**: SSL/TLS enforced for all connections
4. **Regular backups**: Automated backups with encryption

### Connection Security

```python
# Connection pooling with limits
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 10

# Connection timeout
DATABASE_TIMEOUT = 30
```

## API Security

### Rate Limiting

Redis-backed rate limiting with configurable limits:

```python
# Production settings
RATE_LIMIT_CALLS = 100
RATE_LIMIT_PERIOD = 60  # seconds
ENABLE_RATE_LIMITING = true
```

### CORS Configuration

Restrictive CORS settings for production:

```python
# Only allow specific origins
ALLOWED_ORIGINS = [
    "https://your-domain.com",
    "https://www.your-domain.com"
]

# Disable credentials for public endpoints
ALLOW_CREDENTIALS = false
```

### Input Validation

All API inputs are validated using Pydantic models:

```python
from pydantic import BaseModel, validator

class AudioUpload(BaseModel):
    filename: str
    size: int
    
    @validator('size')
    def validate_size(cls, v):
        if v > 100_000_000:  # 100MB limit
            raise ValueError('File too large')
        return v
```

### Authentication & Authorization

1. **API Keys**: Secure API key validation
2. **JWT Tokens**: Short-lived tokens with refresh mechanism
3. **Role-based access**: Different permissions for different user types

## Container Security

### Docker Best Practices

1. **Non-root user**: Application runs as non-root user
   ```dockerfile
   RUN adduser --disabled-password --gecos '' appuser
   USER appuser
   ```

2. **Minimal base image**: Using `python:3.11-slim`
3. **Layer optimization**: Multi-stage builds for smaller images
4. **Security scanning**: Regular vulnerability scans

### Container Networking

1. **Internal networks**: Services communicate through internal Docker networks
2. **Port exposure**: Only necessary ports exposed to host
3. **Service isolation**: Each service in separate container

## Network Security

### HTTPS Configuration

1. **SSL/TLS termination**: Nginx handles SSL termination
2. **Certificate management**: Let's Encrypt or commercial certificates
3. **HSTS headers**: Strict Transport Security enabled

### Firewall Rules

```bash
# Allow only necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP (redirect to HTTPS)
ufw allow 443/tcp   # HTTPS
ufw deny 6379/tcp   # Redis (internal only)
ufw deny 5432/tcp   # PostgreSQL (internal only)
```

## Monitoring & Auditing

### Security Monitoring

1. **Log analysis**: Structured logging with security events
2. **Intrusion detection**: Failed login attempts, unusual patterns

### Audit Tools

Run security audits regularly:

```bash
# Security audit script
python security_audit.py

# Dependency vulnerability scan
pip-audit

# Container security scan
docker scan studymate-api
```

### Log Management

```python
# Security-focused logging
logging.config.dictConfig({
    'version': 1,
    'handlers': {
        'security': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/studymate/security.log',
            'formatter': 'detailed'
        }
    },
    'loggers': {
        'security': {
            'handlers': ['security'],
            'level': 'INFO'
        }
    }
})
```

## Deployment Security

### Pre-deployment Checklist

- [ ] Run security audit: `python security_audit.py`
- [ ] Update all dependencies
- [ ] Generate secure secrets: `python setup_production.py`
- [ ] Configure SSL certificates
- [ ] Set up monitoring and alerting
- [ ] Test backup and recovery procedures
- [ ] Configure firewall rules
- [ ] Review access controls

### Production Environment

1. **Environment isolation**: Separate production environment
2. **Access control**: Limited SSH access, key-based authentication
3. **Regular updates**: Automated security updates
4. **Backup strategy**: Automated backups with encryption

### Docker Compose Security

```yaml
# Secure docker-compose.yml
services:
  studymate-api:
    # Use specific image tags, not 'latest'
    image: studymate-api:1.0.0
    
    # Drop capabilities
    cap_drop:
      - ALL
    
    # Read-only root filesystem
    read_only: true
    
    # Limit resources
    mem_limit: 512m
    cpus: 0.5
```

## Security Incident Response

### Incident Response Plan

1. **Detection**: Automated alerts for security events
2. **Assessment**: Severity classification and impact analysis
3. **Containment**: Isolate affected systems
4. **Recovery**: Restore services and data
5. **Lessons learned**: Post-incident review and improvements

### Emergency Procedures

```bash
# Emergency shutdown
docker-compose down

# Reset database (if compromised)
docker-compose down -v
docker-compose up -d postgres
# Restore from backup

# Rotate all secrets
python setup_production.py
docker-compose up -d --build
```

## Compliance & Standards

### Security Standards

- **OWASP Top 10**: Protection against common vulnerabilities
- **CIS Controls**: Implementation of security best practices
- **NIST Framework**: Security framework compliance

### Data Protection

- **Data encryption**: At rest and in transit
- **Data retention**: Automated cleanup of old data
- **Privacy controls**: User data protection and consent

## Regular Security Tasks

### Daily
- Review security logs
- Monitor system performance
- Check for failed authentication attempts

### Weekly
- Update dependencies
- Review access logs
- Test backup procedures

### Monthly
- Security audit: `python security_audit.py`
- Penetration testing
- Access control review

### Quarterly
- Rotate secrets and passwords
- Security training for team
- Incident response drill

## Security Contacts

- **Security Team**: security@studymate.com
- **Emergency**: +1-XXX-XXX-XXXX
- **Incident Reporting**: incidents@studymate.com

---

## Quick Reference

### Security Commands

```bash
# Run security audit
python security_audit.py

# Setup production environment
python setup_production.py

# Check container security
docker scan studymate-api

# Update dependencies
pip-audit --fix

# Generate secure password
python -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%^&*') for _ in range(32)))"
```

### Environment Variables Checklist

- [ ] `POSTGRES_PASSWORD` - Strong database password
- [ ] `REDIS_PASSWORD` - Strong Redis password
- [ ] `API_KEY` - Secure API key
- [ ] `OPENAI_API_KEY` - Valid OpenAI API key
- [ ] `ALLOWED_ORIGINS` - Correct domain list
- [ ] `TRUSTED_HOSTS` - Correct host list

### Security Best Practices

1. **Never hardcode secrets** in source code
2. **Use environment variables** for all configuration
3. **Implement proper logging** for security events
4. **Regular security audits** and penetration testing
5. **Keep dependencies updated** and scan for vulnerabilities
6. **Use HTTPS everywhere** in production
7. **Implement proper backup** and recovery procedures
8. **Monitor and alert** on security events
