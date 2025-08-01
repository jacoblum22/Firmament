# File Upload Validation Testing Guide

## Quick Start - How to Verify Your Upload Security is Working

### 1. **Automated Testing (Recommended)**

Run the comprehensive test suite:

```bash
# Navigate to backend directory
cd backend

# Run all tests
python tests/run_upload_tests.py

# Or run specific test types
python tests/run_upload_tests.py --unit-only          # Just unit tests
python tests/run_upload_tests.py --integration-only  # Just integration tests
python tests/run_upload_tests.py --verbose           # Show detailed output
```

### 2. **Manual Testing with Running Server**

Start your backend server:

```bash
cd backend
python -m uvicorn main:app --reload
```

In another terminal, run manual tests:

```bash
cd backend
python tests/manual_upload_test.py

# Or quick test (faster)
python tests/manual_upload_test.py --quick
```

### 3. **Individual Test Components**

Test specific components:

```bash
# Test file validator utility
python -m pytest tests/utils/test_file_validator.py -v

# Test upload endpoint integration
python -m pytest tests/integration/test_file_upload_validation.py -v

# Test comprehensive suite
python -m pytest tests/test_file_upload_comprehensive.py -v
```

---

## 🧪 What Tests Are Included

### **Unit Tests** (`tests/utils/test_file_validator.py`)
- ✅ File extension validation
- ✅ File size limits enforcement
- ✅ File signature/magic number checking
- ✅ Filename security validation
- ✅ Path traversal prevention
- ✅ Malformed file detection

### **Integration Tests** (`tests/integration/test_file_upload_validation.py`)
- ✅ Complete upload endpoint testing
- ✅ Valid file uploads (PDF, MP3, WAV, TXT, M4A)
- ✅ Malicious file rejection
- ✅ Oversized file rejection
- ✅ File type spoofing detection
- ✅ Filename sanitization
- ✅ Error handling

### **Comprehensive Tests** (`tests/test_file_upload_comprehensive.py`)
- ✅ Performance testing with large files
- ✅ Concurrent upload testing
- ✅ Memory usage validation
- ✅ Unicode filename handling
- ✅ Stress testing
- ✅ Edge case handling

### **Manual Tests** (`tests/manual_upload_test.py`)
- ✅ Real server testing
- ✅ Generated test files
- ✅ Interactive validation
- ✅ Detailed reporting

---

## 📋 Expected Test Results

### ✅ **Tests That Should PASS**
- Valid PDF uploads (< 50MB)
- Valid audio uploads (MP3 < 200MB, WAV < 500MB)
- Valid text uploads (< 10MB)
- Proper filename sanitization
- Files with correct content signatures

### ❌ **Tests That Should FAIL (Security Working)**
- Executable files (.exe, .bat)
- Files over size limits
- Files with mismatched content/extension
- Malicious filenames (path traversal attempts)
- Empty files
- Files with dangerous content

---

## 🔍 Interpreting Results

### **All Tests Pass**
```
🎉 All tests passed! Your file upload validation is working correctly.
Success rate: 100%
```
**Meaning**: Your security implementation is robust and working as expected.

### **Some Tests Fail**
```
⚠️ Some tests failed. Please review the output above.
Success rate: 85%
```
**Meaning**: There may be configuration issues or bugs. Check the detailed output.

### **Many Tests Fail**
```
❌ Critical issues detected.
Success rate: < 70%
```
**Meaning**: Significant problems with the upload validation. Review implementation.

---

## 🛠️ Troubleshooting Common Issues

### **Import Errors**
```bash
ModuleNotFoundError: No module named 'utils.file_validator'
```
**Solution**: Make sure you're running from the `backend` directory.

### **Server Connection Errors**
```bash
❌ Cannot reach server: Connection refused
```
**Solution**: Start the backend server first:
```bash
python -m uvicorn main:app --reload
```

### **File Size Test Failures**
```bash
❌ FAIL - Oversized file should be rejected but was accepted
```
**Solution**: Check that file size validation is properly implemented in routes.py.

### **Permission Errors on Windows**
```bash
PermissionError: [WinError 32] The process cannot access the file
```
**Solution**: Close any open file handles or run as administrator.

---

## 📊 Performance Benchmarks

### **Expected Performance**
- File validation: < 1 second for files under 10MB
- Upload processing: < 5 seconds for files under 50MB
- Memory usage: < 2x file size during validation

### **Performance Test**
```bash
python tests/run_upload_tests.py --performance
```

---

## 🔐 Security Verification Checklist

Use this checklist to manually verify security:

### File Type Security
- [ ] `.exe` files are rejected
- [ ] `.zip` files disguised as PDFs are rejected
- [ ] Files with wrong extensions are caught
- [ ] Only allowed extensions (.pdf, .mp3, .wav, .txt, .m4a) work

### File Size Security
- [ ] 60MB PDF is rejected (limit: 50MB)
- [ ] 15MB text file is rejected (limit: 10MB)
- [ ] 250MB MP3 is rejected (limit: 200MB)
- [ ] Files just under limits are accepted

### Filename Security
- [ ] `../../../etc/passwd.pdf` is sanitized or rejected
- [ ] `file<script>.pdf` is sanitized
- [ ] `normal_file.pdf` works fine
- [ ] Unicode filenames are handled properly

### Content Security
- [ ] PDF with executable content is rejected
- [ ] MP3 with valid header is accepted
- [ ] WAV with proper RIFF structure is accepted
- [ ] Corrupted files are detected

---

## 🚀 Quick Commands Reference

```bash
# Run everything (recommended first test)
python tests/run_upload_tests.py

# Fast unit tests only
python tests/run_upload_tests.py --unit-only

# Test against running server
python tests/manual_upload_test.py --quick

# Generate test files for manual inspection
python -c "from tests.utils.test_file_generators import TestFileGenerator; print(TestFileGenerator.save_test_files_to_disk('./test_files'))"

# Check specific component
python -m pytest tests/utils/test_file_validator.py::TestFileValidator::test_validate_upload_oversized_file -v
```

---

## 📈 Continuous Testing

### **For Development**
Add to your development workflow:
```bash
# Before committing changes
python tests/run_upload_tests.py --unit-only

# Before deploying
python tests/run_upload_tests.py --manual
```

### **For CI/CD**
Add to your CI pipeline:
```yaml
- name: Test File Upload Validation
  run: |
    cd backend
    python tests/run_upload_tests.py --unit-only --integration-only
```

### **For Production Monitoring**
Run periodic tests:
```bash
# Weekly security check
python tests/manual_upload_test.py --quick
```

---

This testing suite ensures your file upload validation is bulletproof! 🛡️
