import sys
import os

# Add the backend directory to the Python path for test imports
backend_dir = os.path.dirname(os.path.dirname(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
