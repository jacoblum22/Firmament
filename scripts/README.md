# scripts/

Production deployment and operations scripts. These are **not** part of the application runtime — they are run manually as needed.

Run all scripts from the **project root** (not from inside `scripts/`).

| Script | Purpose | When to use |
|--------|---------|-------------|
| `cleanup_files.py` | Safely deletes old uploads, output, and temp files; supports `--dry-run`, `--status`, `--temp-only` | Periodically or when disk space is low |
| `deploy.py` | Production deployment: validates config, installs deps, runs security checks, starts uvicorn | Deploying to a production server (non-Docker) |
| `security_audit.py` | Scans `docker-compose.yml` and `.env` files for hardcoded secrets; writes a report to stdout | Before deploying; after changing env config |
| `setup_production.py` | Generates cryptographically-secure passwords and patches them into `backend/.env.production` | Once, before the first production deployment |

## Usage

```bash
# From project root:
python scripts/cleanup_files.py --status
python scripts/cleanup_files.py --dry-run
python scripts/deploy.py
python scripts/deploy.py --start
python scripts/security_audit.py
python scripts/setup_production.py
```

## Diagnostic & Manual Test Scripts

Diagnostic and manual QA scripts live in `backend/tests/manual/`:

| Script | Purpose |
|--------|---------|
| `debug_config.py` | Loads production config and prints every setting value for manual inspection |
| `frontend_upload_probe.py` | Sends valid and malformed upload requests to verify request handling |
| `manual_upload_test.py` | Generates test files and runs upload validation scenarios against a live server |
| `quick_test.py` | Smoke-tests config loading, S3 storage, auth, and content hash logic |

```bash
python backend/tests/manual/debug_config.py
python backend/tests/manual/frontend_upload_probe.py --server-url http://localhost:8000
python backend/tests/manual/manual_upload_test.py --server-url http://localhost:8000
python backend/tests/manual/quick_test.py
```

## Not suitable for CI

These scripts require local `.env` files or real credentials. For automated testing, use pytest:

```bash
pytest backend/tests/ -v
```
