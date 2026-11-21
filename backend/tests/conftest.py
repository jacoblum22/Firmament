import sys
import os
from pathlib import Path

# Add the backend directory to the Python path for test imports
backend_dir = os.path.dirname(os.path.dirname(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# These files are standalone scripts (not pytest tests) that call sys.exit() at
# module level, which crashes pytest collection.  Tell pytest to ignore them.
collect_ignore = [
    str(Path(__file__).parent / "utils" / "test_cluster_analysis.py"),
    str(Path(__file__).parent / "integration" / "test_s3_production.py"),
    str(Path(__file__).parent / "integration" / "test_s3_connection.py"),
]
