"""Utilities package with organized subpackages and backward-compatible aliases."""

import sys

# Backward-compatible re-exports — import from subpackages
from utils.audio import *
from utils.common import *
from utils.nlp import *
from utils.security import *
from utils.storage import *

from .audio import preprocess_audio as _preprocess_audio
from .audio import rnnoise_process as _rnnoise_process
from .audio import transcribe_audio as _transcribe_audio
from .common import error_messages as _error_messages
from .common import openai_client as _openai_client
from .nlp import bertopic_processor as _bertopic_processor
from .nlp import chunk_size_optimizer as _chunk_size_optimizer
from .nlp import clean_text as _clean_text
from .nlp import expand_bullet_point as _expand_bullet_point
from .nlp import expand_cluster as _expand_cluster
from .nlp import filter_chunks as _filter_chunks
from .nlp import generate_cluster_heading as _generate_cluster_heading
from .nlp import save_bullet_expansion as _save_bullet_expansion
from .nlp import semantic_segmentation as _semantic_segmentation
from .security import auth as _auth
from .security import circuit_breaker as _circuit_breaker
from .security import file_validator as _file_validator
from .storage import cleanup_service as _cleanup_service
from .storage import content_cache as _content_cache
from .storage import file_cleanup as _file_cleanup
from .storage import s3_storage as _s3_storage
from .storage import secure_temp_files as _secure_temp_files

# Backward-compatible flat module aliases (for imports like `from utils.auth import ...`).
sys.modules.setdefault(__name__ + ".auth", _auth)
sys.modules.setdefault(__name__ + ".circuit_breaker", _circuit_breaker)
sys.modules.setdefault(__name__ + ".file_validator", _file_validator)
sys.modules.setdefault(__name__ + ".error_messages", _error_messages)
sys.modules.setdefault(__name__ + ".openai_client", _openai_client)
sys.modules.setdefault(__name__ + ".preprocess_audio", _preprocess_audio)
sys.modules.setdefault(__name__ + ".rnnoise_process", _rnnoise_process)
sys.modules.setdefault(__name__ + ".transcribe_audio", _transcribe_audio)
sys.modules.setdefault(__name__ + ".bertopic_processor", _bertopic_processor)
sys.modules.setdefault(__name__ + ".chunk_size_optimizer", _chunk_size_optimizer)
sys.modules.setdefault(__name__ + ".clean_text", _clean_text)
sys.modules.setdefault(__name__ + ".filter_chunks", _filter_chunks)
sys.modules.setdefault(__name__ + ".generate_cluster_heading", _generate_cluster_heading)
sys.modules.setdefault(__name__ + ".semantic_segmentation", _semantic_segmentation)
sys.modules.setdefault(__name__ + ".expand_bullet_point", _expand_bullet_point)
sys.modules.setdefault(__name__ + ".expand_cluster", _expand_cluster)
sys.modules.setdefault(__name__ + ".save_bullet_expansion", _save_bullet_expansion)
sys.modules.setdefault(__name__ + ".content_cache", _content_cache)
sys.modules.setdefault(__name__ + ".file_cleanup", _file_cleanup)
sys.modules.setdefault(__name__ + ".cleanup_service", _cleanup_service)
sys.modules.setdefault(__name__ + ".s3_storage", _s3_storage)
sys.modules.setdefault(__name__ + ".secure_temp_files", _secure_temp_files)
