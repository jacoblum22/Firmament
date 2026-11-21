from fastapi import APIRouter

from .auth import router as auth_router
from .constants import BASE_DIR, JOB_STATUS, OUTPUT_DIR, PROCESSED_DIR, UPLOAD_DIR, set_status
from .expansion import router as expansion_router
from .health import router as health_router
from .processing import router as processing_router
from .upload import router as upload_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(upload_router)
router.include_router(processing_router)
router.include_router(expansion_router)
router.include_router(health_router)

__all__ = [
    "router",
    "BASE_DIR",
    "UPLOAD_DIR",
    "OUTPUT_DIR",
    "PROCESSED_DIR",
    "JOB_STATUS",
    "set_status",
]
