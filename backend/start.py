#!/usr/bin/env python3
"""
StudyMate API Launcher
Run the FastAPI application with environment-specific configurations.
"""

import os
import sys
import uvicorn
import argparse
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from config import settings


def main():
    parser = argparse.ArgumentParser(description="Launch StudyMate API")
    parser.add_argument(
        "--env",
        choices=["development", "production"],
        default="development",
        help="Environment to run in (default: development)",
    )
    parser.add_argument(
        "--host", default=None, help="Host to bind to (overrides config)"
    )
    parser.add_argument(
        "--port", type=int, default=None, help="Port to bind to (overrides config)"
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload (development only)"
    )
    parser.add_argument(
        "--workers", type=int, default=None, help="Number of workers (production only)"
    )

    args = parser.parse_args()

    # Set environment
    os.environ["ENVIRONMENT"] = args.env

    # Reload settings to pick up environment changes
    from config import Settings

    settings_instance = Settings()

    # Configuration
    config = {
        "app": "main:app",
        "host": args.host or settings_instance.host,
        "port": args.port or settings_instance.port,
        "log_level": settings_instance.log_level.lower(),
    }

    # Environment-specific settings
    if args.env == "development":
        config.update(
            {
                "reload": args.reload or settings_instance.reload,
                "access_log": True,
            }
        )
        print(f"🚀 Starting StudyMate API in DEVELOPMENT mode")
        print(f"📍 Server: http://{config['host']}:{config['port']}")
        print(f"📚 Docs: http://{config['host']}:{config['port']}/docs")
        print(f"🔄 Auto-reload: {config['reload']}")

    elif args.env == "production":
        config.update(
            {
                "workers": args.workers or settings_instance.workers,
                "access_log": False,
            }
        )
        print(f"🚀 Starting StudyMate API in PRODUCTION mode")
        print(f"📍 Server: http://{config['host']}:{config['port']}")
        print(f"👥 Workers: {config['workers']}")
        print(f"🔐 Security: Enhanced")

    print(f"🌍 Environment: {args.env}")
    print(f"🎯 Debug: {settings_instance.debug}")
    print(f"📝 Log Level: {settings_instance.log_level}")
    print("-" * 50)

    # Start the server
    uvicorn.run(**config)


if __name__ == "__main__":
    main()
