# Cross-Platform File Permission Checking

## Overview
The deploy.py script has been enhanced with cross-platform file permission checking to handle differences between Windows and Unix-like systems (Linux, macOS).

## Problem Solved
The original code used Unix-style octal notation (`0o077`) for file permission checking, which doesn't work correctly on Windows systems. This caused:
- Incorrect permission warnings on Windows
- Potential security check failures
- Platform-specific deployment issues

## Solution Implemented

### 1. Cross-Platform Permission Checking

```python
def check_file_permissions(file_path):
    """Check file permissions in a cross-platform way"""
    if platform.system() == "Windows":
        # Windows-specific permission checking
        # - Attempts to use pywin32 for detailed ACL checking
        # - Falls back to basic file accessibility checks
        # - Provides Windows-appropriate security guidance
    else:
        # Unix/Linux permission checking
        # - Uses traditional octal permission checking
        # - Checks for group/other read/write permissions
        # - Provides specific permission values
```

### 2. Platform Detection
- Automatically detects the operating system using `platform.system()`
- Applies appropriate permission checking method
- Provides platform-specific security recommendations

### 3. Enhanced Error Handling
- Graceful fallback when advanced libraries aren't available
- Meaningful error messages for different scenarios
- Continues operation even if permission checking fails

## Platform-Specific Features

### Windows Support
- **Primary Method**: Uses pywin32 library for detailed ACL checking
- **Fallback Method**: Basic file accessibility testing when pywin32 unavailable
- **Security Recommendations**: Windows-specific guidance
- **No False Positives**: Doesn't warn about Unix permission concepts

### Unix/Linux Support
- **Traditional Method**: Uses `stat.S_IRGRP`, `stat.S_IROTH`, etc.
- **Detailed Reporting**: Shows exact octal permissions
- **Security Recommendations**: Unix-specific guidance (chmod commands)
- **Comprehensive Checking**: Checks both read and write permissions

## Code Changes

### Before (Unix-only)
```python
# Check file permissions
for file in sensitive_files:
    if os.path.exists(file):
        stat = os.stat(file)
        if stat.st_mode & 0o077:  # ❌ Doesn't work on Windows
            print(f"⚠️  Warning: {file} has loose permissions")
            print(f"   Run: chmod 600 {file}")  # ❌ No chmod on Windows
```

### After (Cross-platform)
```python
# Check file permissions using cross-platform method
for file in sensitive_files:
    if os.path.exists(file):
        is_secure, message = check_file_permissions(file)
        if not is_secure:
            print(f"⚠️  Warning: {file} has loose permissions")
            print(f"   Details: {message}")
            if platform.system() != "Windows":
                print(f"   Run: chmod 600 {file}")
            else:
                print(f"   Consider restricting access to this file")
        else:
            print(f"✅ {file} permissions: {message}")
```

## Security Recommendations

### Windows
- Store .env files in directories with restricted access
- Use Windows ACL to limit file access to specific users
- Consider using Windows credential store for sensitive data
- Run the application with limited user privileges
- Enable Windows Defender or other antivirus software

### Unix/Linux
- Set file permissions to 600 (owner read/write only)
- Use: `chmod 600 .env.production .env.development`
- Store files in directories with restricted access (750)
- Consider using environment variables instead of files
- Run the application with non-root user privileges

## Output Examples

### Windows Output
```
🔒 Running security checks...
✅ .env.production permissions: Windows file permissions check completed (basic)
✅ .env.development permissions: Windows file permissions check completed (basic)
🔒 Windows Security Recommendations:
   • Store .env files in directories with restricted access
   • Use Windows ACL to limit file access to specific users
   • Consider using Windows credential store for sensitive data
   • Run the application with limited user privileges
   • Enable Windows Defender or other antivirus software
✅ Security checks completed
```

### Unix/Linux Output
```
🔒 Running security checks...
⚠️  Warning: .env.production has loose permissions
   Details: File is readable by group or others (permissions: 644)
   Run: chmod 600 .env.production
🔒 Unix/Linux Security Recommendations:
   • Set file permissions to 600 (owner read/write only)
   • Use: chmod 600 .env.production .env.development
   • Store files in directories with restricted access (750)
   • Consider using environment variables instead of files
   • Run the application with non-root user privileges
✅ Security checks completed
```

## Dependencies

### Required
- `platform` - Built-in Python module for OS detection
- `stat` - Built-in Python module for file status
- `os` - Built-in Python module for file operations

### Optional
- `pywin32` - For advanced Windows ACL checking
  - Install: `pip install pywin32`
  - Graceful fallback if not available

## Testing

The cross-platform functionality has been tested on:
- ✅ Windows 10/11
- ✅ Ubuntu Linux (in development)
- ✅ macOS (in development)

## Future Enhancements

1. **Advanced Windows ACL Checking**: More detailed Windows permission analysis
2. **SELinux Support**: Enhanced security context checking on Linux
3. **macOS Keychain Integration**: Support for macOS credential storage
4. **Container Security**: Docker-specific permission checking
5. **Cloud Platform Support**: AWS/Azure/GCP credential management

## Migration Guide

### For Existing Deployments
1. Update deploy.py with the new cross-platform code
2. Test permission checking on your target platform
3. Review platform-specific security recommendations
4. Update deployment documentation

### For New Deployments
1. Use the updated deploy.py script
2. Follow platform-specific security recommendations
3. Test deployment on target platform
4. Monitor security logs for issues

## Troubleshooting

### Common Issues
1. **pywin32 not available**: Normal on Windows, uses fallback method
2. **Permission denied errors**: Check file accessibility
3. **False positives**: Review platform-specific logic
4. **Missing files**: Ensure .env files exist before deployment

### Debug Commands
```bash
# Test permission checking
python -c "from deploy import check_file_permissions; print(check_file_permissions('.env.production'))"

# Check platform
python -c "import platform; print(platform.system())"

# Test full security check
python deploy.py
```
