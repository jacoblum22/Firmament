# scripts/

Developer utility scripts. These are **not** part of the application runtime — they are run manually as needed.

Run all scripts from the **project root** (not from inside `scripts/`).

| Script | Purpose | When to use |
|--------|---------|-------------|
| `debug_config.py` | Loads production config and prints every setting value for manual inspection | When diagnosing config loading issues in production |
| `security_audit.py` | Scans `docker-compose.yml` and `.env` files for hardcoded secrets; writes a report to stdout | Before deploying; after changing env config |
| `quick_test.py` | Smoke-tests config loading, S3 storage manager, auth manager, and content hash logic | After new environment setup or major dependency changes |

## Usage

```bash
# From project root:
python scripts/debug_config.py
python scripts/security_audit.py
python scripts/quick_test.py
```

## Not suitable for CI

These scripts require local `.env` files or real credentials. For automated testing, use pytest:

```bash
pytest backend/tests/ -v
```
