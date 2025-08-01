# Firmament Backend CORS Configuration

## Environment Setup

### Development
1. Copy `.env.example` to `.env.development`
2. Update the `ALLOWED_ORIGINS` to include your development frontend URLs
3. Set `ENVIRONMENT=development`

### Production
1. Copy `.env.example` to `.env.production`
2. Update `ALLOWED_ORIGINS` with your production domain(s)
3. Set `ENVIRONMENT=production`
4. Update `TrustedHostMiddleware` allowed hosts in `main.py`

## CORS Configuration

### Development Settings
- Allows multiple localhost origins (5173, 3000, etc.)
- Permissive settings for development convenience
- Debug mode enabled

### Production Settings
- Strict origin validation
- Security headers enabled
- Rate limiting enabled
- HTTPS enforcement headers

## Security Features

### Headers Added in Production
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy: default-src 'self'`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`

### Rate Limiting
- 100 requests per minute per IP in production
- Configurable in `middleware.py`

## Deployment Checklist

### Before Deployment
1. [ ] Update `.env.production` with actual domain names
2. [ ] Update `TrustedHostMiddleware` allowed hosts
3. [ ] Set `ENVIRONMENT=production`
4. [ ] Ensure HTTPS is configured
5. [ ] Test CORS with production domains

### Environment Variables
```bash
# Required
ENVIRONMENT=production
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Optional
DEBUG=False
ALLOW_CREDENTIALS=true
API_KEY=your-secure-api-key
SECURE_HEADERS=true
```

## Testing CORS

### Development
```bash
curl -H "Origin: http://localhost:5173" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     http://localhost:8000/
```

### Production
```bash
curl -H "Origin: https://yourdomain.com" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     https://api.yourdomain.com/
```

## Common Issues

### CORS Error in Browser
- Check that frontend origin is in `ALLOWED_ORIGINS`
- Verify environment file is loaded correctly
- Check browser developer tools for specific error

### 429 Rate Limit
- Increase rate limit in `middleware.py`
- Implement user-based rate limiting for authenticated users
- Consider using Redis for distributed rate limiting

### Security Headers
- Adjust CSP policy if needed for your application
- Test with your specific deployment setup
- Consider using a CDN for additional security
