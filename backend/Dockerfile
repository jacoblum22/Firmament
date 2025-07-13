# Production Dockerfile for StudyMate API
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT=production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY --chown=appuser:appuser requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data to avoid runtime downloads (only if NLTK is installed)
RUN python -c "try: import nltk; print('NLTK found, downloading data...'); nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('wordnet', quiet=True); nltk.download('averaged_perceptron_tagger', quiet=True); print('NLTK data downloaded successfully') except ImportError: print('NLTK not installed, skipping data download')" || true

# Copy application code
COPY --chown=appuser:appuser . .

# Create directories for uploads and logs
RUN mkdir -p /var/uploads /var/temp /var/log/studymate

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app /var/uploads /var/temp /var/log/studymate

USER appuser

# Expose port
EXPOSE 8000

# Health check using curl (now available)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Alternative Python-based health check (uncomment to use instead of curl):
# HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
#     CMD python healthcheck.py || exit 1

# Start command
CMD ["python", "start.py", "--env", "production"]
