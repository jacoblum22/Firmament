# Content-Based Caching System

## Overview

Firmament now includes a robust content-based caching system that avoids reprocessing identical files regardless of their filename. This significantly improves performance for duplicate content and provides better reliability than filename-based caching.

## Features

### ✅ Content-Based Identification
- Uses SHA256 hashing of file content to identify identical files
- Works regardless of filename, location, or timestamp
- Handles cases where same content has different filenames
- Prevents false cache hits from files with same name but different content

### ✅ Two-Level Caching
1. **Transcription Cache**: Stores raw transcribed/extracted text
2. **Processed Cache**: Stores fully processed data (segments, topics, clusters)

### ✅ Automatic Cache Management
- Cache statistics and monitoring
- Configurable cleanup of old entries
- Proper error handling and fallbacks
- Maintains index for fast lookups

## How It Works

### Cache Structure
```
cache/
├── transcriptions/
│   ├── [content_hash].txt       # Raw transcription text  
│   └── [content_hash].meta.json # Metadata (filename, timestamp, etc.)
├── processed/
│   ├── [content_hash].json      # Processed data (segments, clusters, etc.)
│   └── [content_hash].meta.json # Metadata
└── index.json                   # Cache index for quick lookups
```

### Processing Flow
1. File uploaded → Content hash calculated
2. Check for processed cache → Return immediately if found
3. Check for transcription cache → Skip transcription if found
4. Perform transcription/extraction → Save to transcription cache
5. Perform topic analysis → Save to processed cache
6. Return results with cache info

## API Endpoints

### Cache Statistics
```http
GET /cache/stats
```

Returns cache statistics including:
- Total cache entries
- Transcription vs processed entries  
- Total cache size
- Creation and cleanup timestamps

### Cache Cleanup
```http
POST /cache/cleanup
Content-Type: application/json

{
  "max_age_days": 30
}
```

Removes cache entries older than the specified number of days.

## Performance Benefits

### Before (Filename-Based)
- ❌ Same content with different filenames processed multiple times
- ❌ Different content with same filename caused cache collisions  
- ❌ Moving/renaming files invalidated cache
- ❌ No protection against partial cache corruption

### After (Content-Based)
- ✅ Identical content cached once regardless of filename
- ✅ No false cache hits from filename collisions
- ✅ Robust against file operations and corruption
- ✅ Automatic cache validation and error recovery

## Configuration

The caching system works out of the box with no configuration required. However, you can customize:

### Cache Directory
By default, cache is stored in `cache/` directory. You can change this:

```python
from utils.content_cache import ContentCache

cache = ContentCache(base_cache_dir="my_custom_cache_dir")
```

### Cache Cleanup
You can configure automatic cleanup by calling:

```python
cache.cleanup_old_entries(max_age_days=30)
```

## Monitoring and Maintenance

### Check Cache Status
```bash
curl http://localhost:8000/cache/stats
```

### Manual Cache Cleanup
```bash
curl -X POST http://localhost:8000/cache/cleanup \
  -H "Content-Type: application/json" \
  -d '{"max_age_days": 30}'
```

### Log Messages
The caching system provides detailed logging:

```
[12345678] Found cached transcription (content hash: 51d698da...)
[12345678] Saved transcription to content cache (hash: 51d698da...)
[12345678] Found cached processed data (content hash: 51d698da...)
```

## Error Handling

The caching system is designed to fail gracefully:
- If cache read fails → Continues with normal processing
- If cache write fails → Logs warning but continues
- If cache directory inaccessible → Falls back to no caching
- Corrupted cache entries are automatically skipped

## Backward Compatibility

The new system maintains compatibility with existing filename-based caches:
1. Checks new content-based cache first
2. Falls back to legacy filename-based cache if found
3. Gradually migrates to content-based system as files are reprocessed

## Testing

Run the cache test suite:

```bash
python test_cache.py
```

This verifies:
- Cache save/retrieve operations
- Content hash generation
- Cache statistics
- Error handling
- Cleanup functionality

## Migration from Filename-Based Caching

No manual migration is required. The system will:
1. Continue using existing filename-based caches when available
2. Create new content-based caches for new uploads
3. Gradually replace filename-based caches as content is reprocessed
4. Existing cache files can be cleaned up manually if desired

## Best Practices

### For Developers
- Always use the global cache instance: `get_content_cache()`
- Check cache before expensive operations
- Save cache after successful processing  
- Handle cache errors gracefully

### For System Administrators
- Monitor cache size with `/cache/stats` endpoint
- Set up periodic cache cleanup
- Include cache directory in backup strategies
- Monitor logs for cache-related errors

## Troubleshooting

### Cache Not Working
1. Check file permissions on cache directory
2. Verify sufficient disk space
3. Check logs for cache-related errors
4. Test with `test_cache.py` script

### High Cache Usage
1. Run cache cleanup: `POST /cache/cleanup`
2. Check for very large files causing bloat
3. Adjust `max_age_days` for more aggressive cleanup
4. Monitor with cache statistics endpoint

### Performance Issues
1. Ensure cache directory is on fast storage
2. Check if cache index file is corrupted
3. Monitor cache hit/miss ratios in logs
4. Consider cache directory cleanup
