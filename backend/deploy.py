#!/usr/bin/env python3
"""
Production deployment script for StudyMate backend
"""
import os
import sys
import subprocess
from pathlib import Path


def check_environment():
    """Check if production environment is properly configured"""
    print("🔍 Checking production environment...")

    # Check if .env.production exists
    env_file = Path(".env.production")
    if not env_file.exists():
        print("❌ .env.production file not found")
        print("   Please copy .env.example to .env.production and configure it")
        return False

    # Load and check environment variables
    try:
        from dotenv import load_dotenv

        load_dotenv(".env.production")

        required_vars = ["ENVIRONMENT", "ALLOWED_ORIGINS"]
        missing_vars = []

        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            return False

        # Check if still using example values
        origins = os.getenv("ALLOWED_ORIGINS", "")
        if "your-domain.com" in origins:
            print("❌ ALLOWED_ORIGINS still contains example values")
            print("   Please update .env.production with your actual domain")
            return False

        print("✅ Production environment configuration looks good")
        return True

    except Exception as e:
        print(f"❌ Error checking environment: {e}")
        return False


def install_dependencies():
    """Install production dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
            capture_output=True,
        )
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False


def run_security_check():
    """Run basic security checks"""
    print("🔒 Running security checks...")

    # Check file permissions
    sensitive_files = [".env.production", ".env.development"]
    for file in sensitive_files:
        if os.path.exists(file):
            stat = os.stat(file)
            if stat.st_mode & 0o077:  # Check if readable by group/others
                print(f"⚠️  Warning: {file} has loose permissions")
                print(f"   Run: chmod 600 {file}")

    # Check for debug mode
    from dotenv import load_dotenv

    load_dotenv(".env.production")

    if os.getenv("DEBUG", "false").lower() == "true":
        print("⚠️  Warning: DEBUG=True in production environment")

    if os.getenv("ENVIRONMENT") != "production":
        print("⚠️  Warning: ENVIRONMENT is not set to 'production'")

    print("✅ Security checks completed")


def start_server():
    """Start the production server"""
    print("🚀 Starting production server...")

    # Set environment
    os.environ["ENVIRONMENT"] = "production"

    # Start with uvicorn
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--workers",
        "4",
        "--no-reload",
    ]

    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd)


def main():
    """Main deployment function"""
    print("🎯 StudyMate Backend Production Deployment")
    print("=" * 50)

    if not check_environment():
        sys.exit(1)

    if not install_dependencies():
        sys.exit(1)

    run_security_check()

    print("\n🎉 Ready to start production server!")
    print("To start the server, run: python deploy.py --start")

    if "--start" in sys.argv:
        start_server()


if __name__ == "__main__":
    main()
