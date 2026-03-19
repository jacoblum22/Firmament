# Manual QA & Diagnostic Scripts

Scripts for manual testing, debugging, and diagnostics. These require a running server or local `.env` files and are **not** run by pytest.

Run from the **project root**:

```bash
python backend/tests/manual/debug_config.py
python backend/tests/manual/frontend_upload_probe.py --server-url http://localhost:8000
python backend/tests/manual/manual_upload_test.py --server-url http://localhost:8000
python backend/tests/manual/quick_test.py
```

| Script | Purpose |
|--------|---------|
| `debug_config.py` | Loads production config and prints every setting for manual inspection |
| `frontend_upload_probe.py` | Sends valid and malformed upload requests to verify request handling |
| `manual_upload_test.py` | Generates test files and runs upload validation against a live server |
| `quick_test.py` | Smoke-tests config loading, S3, auth, and content hash logic |
