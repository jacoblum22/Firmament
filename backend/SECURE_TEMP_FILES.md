# Secure Temporary File Handling - Security Improvements

## Overview

This document outlines the security improvements implemented for temporary file handling in StudyMate-v2, addressing vulnerabilities in the original implementation around lines 445-458 in `backend/routes.py`.

## Security Issues Addressed

### 1. **Insecure File Permissions**
- **Problem**: Temporary files were created with default system permissions, potentially allowing other users to read sensitive uploaded content.
- **Solution**: Implemented restrictive file permissions (0o600 - owner read/write only) set immediately after file creation.

### 2. **Incomplete Cleanup in Error Paths**
- **Problem**: Temporary files were not properly cleaned up when processing errors occurred, leading to sensitive data lingering on disk.
- **Solution**: Added comprehensive cleanup in all execution paths, including exception handlers.

### 3. **Insecure File Deletion**
- **Problem**: Regular file deletion doesn't securely remove sensitive content from disk (data can be recovered).
- **Solution**: Implemented secure deletion with multiple overwrites using random data before file removal.

### 4. **Disk-based Storage for Sensitive Data**
- **Problem**: All temporary content was written to disk, increasing attack surface.
- **Solution**: Implemented in-memory storage as the primary option, falling back to secure temp files only for large files.

## Implementation Details

### Secure Temporary File Manager (`SecureTempFile`)

```python
from utils.secure_temp_files import SecureTempFile

# Create secure temp file manager
manager = SecureTempFile(
    prefix="studymate_",
    suffix=".bin", 
    secure_delete=True,
    permissions=0o600  # Owner read/write only
)

# Create secure temp file
temp_path = manager.create_temp_file(file_bytes, "unique_id")

# Automatic cleanup with secure deletion
manager.cleanup_file(temp_path, "unique_id")
```

**Key Features:**
- Restrictive permissions set immediately after creation
- Secure multi-pass deletion with random overwrites
- Automatic tracking of created files
- Cross-platform compatibility

### In-Memory Storage (`InMemoryStorage`)

```python
from utils.secure_temp_files import get_memory_storage

memory_storage = get_memory_storage()

# Store content in memory (avoids disk entirely)
if memory_storage.store("unique_id", file_bytes, metadata):
    # Content stored in memory
    content = memory_storage.retrieve("unique_id")
    # ... process content ...
    memory_storage.remove("unique_id")  # Cleanup
```

**Key Features:**
- No disk I/O for small-to-medium files
- Configurable size limits
- Automatic memory management
- Metadata support

### Context Manager for Automatic Cleanup

```python
from utils.secure_temp_files import secure_temp_file

# Guaranteed cleanup even on exceptions
with secure_temp_file(file_bytes, prefix="upload_", suffix=".bin") as temp_path:
    process_file(temp_path)
# File automatically deleted here
```

## Updated Processing Flow

### File Upload Processing (routes.py)

1. **Content Storage Decision**:
   ```python
   # Try memory storage first
   if memory_storage.store(storage_key, file_bytes, metadata):
       storage_type = "memory"
   else:
       # Fallback to secure temp file for large files
       temp_manager = SecureTempFile(permissions=0o600, secure_delete=True)
       temp_path = temp_manager.create_temp_file(file_bytes, storage_key)
       storage_type = "secure_temp"
   ```

2. **Metadata Security**:
   ```python
   # Avoid storing sensitive paths in metadata
   metadata = {
       "temp_storage_type": storage_type,
       "job_id": job_id,  # For cleanup tracking
       # temp_content_file only if using secure_temp
       **({"temp_content_file": temp_path} if storage_type == "secure_temp" else {})
   }
   ```

3. **Comprehensive Error Cleanup**:
   ```python
   except Exception as e:
       # Clean up any temporary storage on error
       if storage_type == "memory":
           memory_storage.remove(storage_key)
       elif temp_manager and temp_path:
           temp_manager.cleanup_file(temp_path, storage_key)
       raise
   ```

### Topic Generation Processing

1. **Flexible Content Retrieval**:
   ```python
   # Handle different storage types
   if temp_storage_type == "memory":
       file_bytes = memory_storage.retrieve(storage_key)
   elif temp_storage_type == "secure_temp":
       with open(temp_file_path, "rb") as f:
           file_bytes = f.read()
   # Legacy support for old temp files
   ```

2. **Secure Cleanup After Processing**:
   ```python
   # Clean up based on storage type
   if temp_storage_type == "memory":
       memory_storage.remove(storage_key)
   elif temp_file_path:
       temp_manager = SecureTempFile(secure_delete=True)
       temp_manager.cleanup_file(temp_file_path)
   ```

## New Management Endpoints

#### Temporary Storage Statistics
```
GET /temp-storage/stats
```
Returns information about memory usage and pending cleanup tasks.

**Security Restrictions:**
- Requires authentication.
- Restricted to users with the admin role or valid service tokens.
- Includes CSRF protection to prevent unauthorized access.

#### Manual Cleanup
```
POST /temp-storage/cleanup
{
    "cleanup_memory": true,
    "cleanup_files": true, 
    "max_age_hours": 24,
    "dry_run": false
}
```
Cleans up orphaned temporary storage (memory and files).

**Security Restrictions:**
- Requires authentication.
- Restricted to users with the admin role or valid service tokens.
- Includes CSRF protection to prevent unauthorized actions.

## Security Benefits

### 1. **Reduced Attack Surface**
- Small-to-medium files never touch disk (memory-only storage)
- Large files use secure temp files with restrictive permissions
- Minimal exposure time on disk

### 2. **Data Protection**
- Secure multi-pass deletion prevents data recovery
- Restrictive file permissions prevent unauthorized access
- In-memory storage eliminates disk-based attacks

### 3. **Comprehensive Cleanup**
- Automatic cleanup in all execution paths
- Manual cleanup endpoints for maintenance
- Orphaned file detection and removal

### 4. **Monitoring and Observability**
- Detailed logging of security operations
- Statistics endpoints for monitoring storage usage
- Cleanup status tracking in metadata

## Configuration Options

### Environment Variables
```python
# In config.py - add these for future enhancement
TEMP_STORAGE_MAX_MEMORY_MB = 100  # Max memory storage per instance
TEMP_FILE_SECURE_DELETE = True   # Enable secure deletion
TEMP_FILE_PERMISSIONS = 0o600    # File permissions (Unix)
TEMP_CLEANUP_MAX_AGE_HOURS = 24  # Auto-cleanup threshold
```

### Storage Thresholds
- **Memory Storage**: Files up to 100MB (configurable)
- **Secure Temp Files**: Files larger than memory limit
- **Auto-cleanup**: Files older than 24 hours

## Testing

Run the security tests:
```bash
cd backend
python -m pytest tests/utils/test_secure_temp_files.py -v
```

Test coverage includes:
- Secure file creation with proper permissions
- Multi-pass secure deletion
- Memory storage limits and cleanup
- Error handling scenarios
- Integration testing

## Migration Notes

### Backwards Compatibility
- Legacy temp files are still supported during cleanup
- Existing metadata files are handled gracefully
- Gradual migration to new secure storage

### Deployment Considerations
- No database changes required
- New utility module must be deployed
- Existing temp files should be cleaned up manually

## Monitoring and Alerting

### Key Metrics to Monitor
- Memory storage usage percentage
- Number of orphaned temp files
- Failed cleanup operations
- Temp file age distribution

### Recommended Alerts
- Memory storage >80% capacity
- Temp files older than 48 hours
- Failed secure deletions
- Excessive temp file creation rate

## Future Enhancements

### Possible Improvements
1. **Encryption**: Add encryption for temp file contents
2. **Compression**: Compress data before storage to save memory/disk
3. **Distributed Storage**: Support for distributed temp storage
4. **Audit Logging**: Enhanced audit trail for compliance

### Configuration Management
- Environment-based storage limits
- Per-user storage quotas
- Configurable cleanup schedules
- Storage backend selection (memory/disk/cloud)
