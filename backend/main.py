from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
from utils.cleanup_scheduler import initialize_cleanup_service, shutdown_cleanup_service
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        # Initialize automated file cleanup service
        # Use "medium" schedule for balanced cleanup (every 6 hours + daily deep clean)
        await initialize_cleanup_service("medium")
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Error during startup: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on shutdown."""
    try:
        await shutdown_cleanup_service()
        logger.info("Application shutdown completed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

@app.get("/")
def read_root():
    return {"message": "MyStudyMate v2 backend is live!"}
