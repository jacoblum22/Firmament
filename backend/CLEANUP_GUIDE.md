# File Cleanup Configuration for StudyMate v2

## Overview

StudyMate v2 now includes a conservative file cleanup system that helps manage disk space while preserving potentially important files. The system is designed with multiple safety mechanisms and is disabled by default.

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file to configure cleanup behavior:

```env
# Enable/disable cleanup service (default: false)
CLEANUP_ENABLED=false

# How often to run cleanup (default: 24 hours)
CLEANUP_INTERVAL_HOURS=24

# Delay before first cleanup after startup (default: 10 minutes)
CLEANUP_STARTUP_DELAY_MINUTES=10

# Age limits (in days/hours)
CLEANUP_TEMP_MAX_AGE_HOURS=24        # Temp files older than 1 day
CLEANUP_UPLOADS_MAX_AGE_DAYS=30      # Uploaded files older than 30 days
CLEANUP_OUTPUT_MAX_AGE_DAYS=90       # Output files older than 90 days  
CLEANUP_PROCESSED_MAX_AGE_DAYS=180   # Processed files older than 6 months

# Size limits (in MB)
CLEANUP_UPLOADS_MAX_SIZE_MB=5000     # 5GB limit for uploads directory
CLEANUP_OUTPUT_MAX_SIZE_MB=2000      # 2GB limit for output directory
CLEANUP_PROCESSED_MAX_SIZE_MB=1000   # 1GB limit for processed directory

# Safety settings
CLEANUP_MIN_FILES_TO_KEEP=5          # Always keep at least 5 newest files
```

## 🛡️ Safety Mechanisms

The cleanup system includes multiple safety features:

### Age-Based Safety
- Never deletes files newer than 1 hour (clock skew protection)
- Conservative default age limits (30-180 days)
- Always keeps minimum number of newest files

### Content-Based Safety
- Skips files with "suspicious" names (backup, important, final, etc.)
- Skips very large files (>1GB) that might be important
- Never deletes files during active processing

### Size-Based Safety
- Only triggers when directories exceed generous size limits
- Removes oldest files first
- Keeps minimum number of files regardless of size

## 📋 Usage Options

### 1. Automatic Background Cleanup (Optional)

Enable in `.env`:
```env
CLEANUP_ENABLED=true
```

The service will:
- Start 10 minutes after application startup
- Run every 24 hours
- Use conservative settings
- Log all activities

### 2. Manual Cleanup via CLI

```bash
# Show current directory status
python cleanup_files.py --status

# Dry run (shows what would be cleaned, default mode)
python cleanup_files.py --dry-run

# Clean only temporary files (safest)
python cleanup_files.py --temp-only --for-real

# Full cleanup with custom settings
python cleanup_files.py --for-real --uploads-max-age 60 --min-keep 10

# See all options
python cleanup_files.py --help
```

### 3. Manual Cleanup via API (Debug Mode Only)

```bash
# Check cleanup service status
curl http://localhost:8000/cleanup/status

# Run dry run cleanup
curl -X POST http://localhost:8000/cleanup/run?dry_run=true

# Run actual cleanup
curl -X POST http://localhost:8000/cleanup/run?dry_run=false
```

## 📊 What Gets Cleaned

### High Priority (Most Aggressive)
- **Temp Chunks**: Audio processing temporary files older than 1 day
- **RNNoise Output**: Audio denoising files when directory > 1GB

### Medium Priority (Conservative)
- **Upload Files**: Original uploaded files older than 30 days
- **Output Files**: Transcription files older than 90 days
- **Processed Files**: Analysis results older than 180 days

### Low Priority (Size-Based Only)
- When directories exceed size limits, oldest files are removed first
- Always keeps minimum number of files regardless of age

## 🚫 What Never Gets Cleaned

- Files newer than 1 hour (safety buffer)
- Files with suspicious names (backup, important, etc.)
- Very large files (>1GB) that might be important user data
- Minimum number of newest files (configurable, default: 5)
- Files during active processing

## 🔍 Monitoring

### Check Directory Status
```bash
python cleanup_files.py --status
```

### Check Service Status (Debug Mode)
```bash
curl http://localhost:8000/cleanup/status
```

### Review Logs
Cleanup activities are logged at INFO level:
```log
2025-07-16 10:00:00 - INFO - Starting conservative file cleanup...
2025-07-16 10:00:01 - INFO - Deleted temp file: temp_chunks/chunk_123.wav
2025-07-16 10:00:01 - INFO - Cleanup complete. Deleted 3 files, freed 45.2MB
```

## 🎯 Recommended Settings

### Development
```env
CLEANUP_ENABLED=false  # Manual cleanup only
```

### Production (Conservative)
```env
CLEANUP_ENABLED=true
CLEANUP_INTERVAL_HOURS=24
CLEANUP_UPLOADS_MAX_AGE_DAYS=60
CLEANUP_OUTPUT_MAX_AGE_DAYS=120
CLEANUP_PROCESSED_MAX_AGE_DAYS=365
```

### Production (Aggressive)
```env
CLEANUP_ENABLED=true
CLEANUP_INTERVAL_HOURS=12
CLEANUP_UPLOADS_MAX_AGE_DAYS=14
CLEANUP_OUTPUT_MAX_AGE_DAYS=30
CLEANUP_PROCESSED_MAX_AGE_DAYS=90
```

## 🔧 Troubleshooting

### Cleanup Not Running
1. Check `CLEANUP_ENABLED=true` in environment
2. Check logs for startup errors
3. Verify service status via API

### Files Not Being Cleaned
1. Check if files meet age criteria
2. Verify files don't match safety patterns
3. Check minimum files to keep setting
4. Review logs for skip reasons

### Too Aggressive Cleanup
1. Increase age limits
2. Increase minimum files to keep
3. Add custom safety patterns
4. Use manual cleanup instead of automatic
