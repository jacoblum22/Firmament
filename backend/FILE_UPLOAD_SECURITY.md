# File Upload Security Guide

## Overview

StudyMate v2 implements comprehensive file upload validation to protect against common security vulnerabilities and ensure reliable file processing.

## Security Features Implemented

### ✅ File Type Validation

**Multiple Layers of Protection:**

1. **Extension Validation**: Only allows `.pdf`, `.mp3`, `.wav`, `.txt`, `.m4a`
2. **MIME Type Checking**: Validates actual file content type
3. **File Signature Validation**: Checks magic numbers to prevent file type spoofing
4. **Frontend Pre-validation**: Client-side checks before upload

### ✅ File Size Limits

**Type-Specific Limits:**

- **PDF Files**: 50MB maximum
- **MP3/M4A Files**: 200MB maximum  
- **WAV Files**: 500MB maximum (uncompressed audio)
- **Text Files**: 10MB maximum

**Configuration Options:**
```env
# Override default size limits (in bytes)
UPLOAD_MAX_SIZE_PDF=52428800      # 50MB
UPLOAD_MAX_SIZE_AUDIO=209715200   # 200MB
UPLOAD_MAX_SIZE_WAV=524288000     # 500MB
UPLOAD_MAX_SIZE_TEXT=10485760     # 10MB
```

### ✅ Malformed File Detection

**Content Validation:**

1. **PDF Files**: Validates PDF header (`%PDF-`)
2. **MP3 Files**: Checks for ID3 tags or MPEG frame headers
3. **WAV Files**: Validates RIFF/WAVE header structure
4. **M4A Files**: Checks for MP4/M4A container signatures

**Security Benefits:**
- Prevents executable files disguised as media files
- Detects corrupted uploads early
- Blocks potential exploit payloads

### ✅ Filename Security

**Path Traversal Prevention:**
- Blocks `../` and `..\\` sequences
- Prevents absolute paths
- Sanitizes dangerous characters

**Character Filtering:**
- Removes: `< > : " | ? * / \\`
- Blocks null bytes (`\x00`)
- Limits filename length (255 chars)

## Implementation Details

### Backend Validation (`utils/file_validator.py`)

```python
from utils.file_validator import FileValidator, FileValidationError

try:
    # Comprehensive validation
    extension, safe_filename = FileValidator.validate_upload(
        file_bytes, filename, max_size_override
    )
except FileValidationError as e:
    # Handle validation error
    return {"error": str(e)}
```

### Frontend Validation (`App.tsx`)

```typescript
const validateFile = (file: File): string | null => {
  // Size check
  if (file.size > maxSize) {
    return `File too large...`;
  }
  
  // Type check
  if (!allowedTypes.includes(fileExtension)) {
    return `Unsupported file type...`;
  }
  
  return null; // Valid
};
```

## Security Test Coverage

### Automated Tests

- ✅ File extension validation
- ✅ File size limit enforcement
- ✅ File signature verification
- ✅ Filename security checks
- ✅ Path traversal prevention
- ✅ Malformed file detection

### Test File Examples

```python
# Test oversized file
large_file = b"x" * (60 * 1024 * 1024)  # 60MB
with pytest.raises(FileValidationError):
    FileValidator.validate_upload(large_file, "large.pdf")

# Test file type spoofing
fake_pdf = b"not a real pdf"
with pytest.raises(FileValidationError):
    FileValidator.validate_upload(fake_pdf, "malicious.pdf")
```

## Configuration Options

### Environment Variables

```env
# File Upload Settings
UPLOAD_MAX_SIZE=104857600              # General size limit (100MB)
UPLOAD_ALLOWED_EXTENSIONS=pdf,mp3,wav,txt,m4a
UPLOAD_VALIDATE_CONTENT=true          # Enable content validation
UPLOAD_DIRECTORY=uploads               # Upload directory
TEMP_DIRECTORY=temp_chunks             # Temporary files
```

### Runtime Configuration

```python
# Access current settings
settings = Settings()
print(f"Max PDF size: {settings.upload_max_size_pdf}")
print(f"Allowed extensions: {settings.upload_allowed_extensions}")
print(f"Content validation: {settings.upload_validate_content}")
```

## Error Handling

### Client-Side Errors

```typescript
// Immediate feedback for users
"File too large. Maximum size: 100MB, your file: 150.5MB"
"Unsupported file type: .exe. Supported types: .pdf, .mp3, .wav, .txt, .m4a"
"File is empty. Please select a valid file."
```

### Server-Side Errors

```python
# Detailed security errors
"File content doesn't match .pdf format. File may be corrupted or have incorrect extension."
"Filename contains dangerous character: <"
"File too large. Maximum size for .wav files: 500.0MB, actual size: 750.2MB"
```

## Performance Considerations

### Optimization Features

1. **Frontend Pre-validation**: Blocks invalid files before upload
2. **Early Validation**: Server checks happen before file processing
3. **Configurable Content Validation**: Can disable signature checking if needed
4. **Stream Processing**: Large files are handled in chunks

### Monitoring

```python
# Log upload attempts for security monitoring
logger.info(f"File upload: {filename} ({file_size}MB) - {validation_result}")
```

## Best Practices

### For Administrators

1. **Regular Limit Review**: Adjust size limits based on usage patterns
2. **Monitor Upload Logs**: Watch for repeated validation failures
3. **Update Signatures**: Keep file signature list current
4. **Test Regularly**: Run security tests on file upload functionality

### For Developers

1. **Never Trust Client Validation**: Always validate server-side
2. **Validate Early**: Check files before processing
3. **Log Security Events**: Record validation failures
4. **Handle Errors Gracefully**: Provide clear user feedback

## Security Compliance

### Standards Met

- ✅ **OWASP File Upload Security**: Comprehensive validation
- ✅ **Content-Type Validation**: Multiple validation layers
- ✅ **File Size Limits**: Prevents resource exhaustion
- ✅ **Path Traversal Prevention**: Secure filename handling
- ✅ **Malware Prevention**: File signature validation

### Risk Mitigation

| Risk | Mitigation |
|------|------------|
| File Type Spoofing | Multi-layer validation (extension + signature) |
| Path Traversal | Filename sanitization and validation |
| Resource Exhaustion | Strict file size limits |
| Malware Upload | Content validation and signature checking |
| Storage Overflow | Automatic cleanup and size monitoring |

## Troubleshooting

### Common Issues

**"File too large" errors:**
- Check file size limits in configuration
- Consider if limits need adjustment for your use case

**"File content doesn't match" errors:**
- File may be corrupted
- File extension may be incorrect
- File may be a different format than expected

**"Unsupported file type" errors:**
- Check allowed extensions configuration
- Verify file has correct extension

### Debug Mode

```env
# Enable detailed validation logging
LOG_LEVEL=DEBUG
```

This will provide detailed information about validation failures in the server logs.
