#!/usr/bin/env python3
"""
Production deployment script for StudyMate backend
"""
import os
import sys
import subprocess
import platform
import stat
from pathlib import Path


def check_file_permissions(file_path):
    """Check file permissions in a cross-platform way"""
    try:
        if platform.system() == "Windows":
            # On Windows, we'll do a basic security check
            try:
                # Try to use pywin32 for detailed permission checking
                import win32security
                import win32file
                import win32con

                # Get file security descriptor
                sd = win32security.GetFileSecurity(
                    file_path, win32security.DACL_SECURITY_INFORMATION
                )
                dacl = sd.GetSecurityDescriptorDacl()

                if dacl is None:
                    return False, "File has no access control (potentially insecure)"

                # Check if Everyone group has access
                everyone_sid = win32security.ConvertStringSidToSid("S-1-1-0")
                for i in range(dacl.GetAceCount()):
                    ace = dacl.GetAce(i)
                    if ace[2] == everyone_sid:
                        return False, "File is accessible by Everyone group"

                return True, "Windows file permissions appear secure"

            except ImportError:
                # pywin32 not available, use basic checks
                file_stat = os.stat(file_path)
                file_path_obj = Path(file_path)

                # Check if file is in a system directory (more secure)
                if file_path_obj.is_absolute():
                    # Check if file is readable by trying to open it
                    try:
                        with open(file_path, "r") as f:
                            pass  # File is readable

                        # Check file size and modification time as basic security indicators
                        if file_stat.st_size > 0:
                            return (
                                True,
                                "Windows file exists and appears accessible (basic check)",
                            )
                        else:
                            return False, "File is empty (potential security issue)"

                    except PermissionError:
                        return True, "File has restricted access (good security)"
                    except Exception as e:
                        return False, f"Error reading file: {e}"

                return True, "Windows file permissions check completed (basic)"

        else:
            # Unix-like systems (Linux, macOS)
            file_stat = os.stat(file_path)

            # Check if file is readable by group or others (octal 077)
            if file_stat.st_mode & (stat.S_IRGRP | stat.S_IROTH):
                return (
                    False,
                    f"File is readable by group or others (permissions: {oct(file_stat.st_mode)[-3:]})",
                )

            # Check if file is writable by group or others
            if file_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
                return (
                    False,
                    f"File is writable by group or others (permissions: {oct(file_stat.st_mode)[-3:]})",
                )

            return (
                True,
                f"File permissions are secure (permissions: {oct(file_stat.st_mode)[-3:]})",
            )

    except Exception as e:
        return False, f"Error checking file permissions: {e}"


def get_security_recommendations():
    """Get platform-specific security recommendations"""
    if platform.system() == "Windows":
        return [
            "🔒 Windows Security Recommendations:",
            "   • Store .env files in directories with restricted access",
            "   • Use Windows ACL to limit file access to specific users",
            "   • Consider using Windows credential store for sensitive data",
            "   • Run the application with limited user privileges",
            "   • Enable Windows Defender or other antivirus software",
        ]
    else:
        return [
            "🔒 Unix/Linux Security Recommendations:",
            "   • Set file permissions to 600 (owner read/write only)",
            "   • Use: chmod 600 .env.production .env.development",
            "   • Store files in directories with restricted access (750)",
            "   • Consider using environment variables instead of files",
            "   • Run the application with non-root user privileges",
        ]


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

        # Import configuration settings for validation
        from config import settings

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

        # Validate configuration settings
        print(f"📋 Configuration validation:")
        print(f"   Environment: {settings.environment}")
        print(f"   Host: {settings.host}")
        print(f"   Port: {settings.port}")
        print(f"   Workers: {settings.workers}")
        print(f"   Debug: {settings.debug}")

        if not settings.is_production:
            print("⚠️  Warning: Environment is not set to production")

        if settings.debug:
            print("⚠️  Warning: Debug mode is enabled in production")

        # Validate port range
        if not (1 <= settings.port <= 65535):
            print(f"❌ Invalid port number: {settings.port}")
            return False

        # Validate workers count
        if settings.workers < 1:
            print(f"❌ Invalid workers count: {settings.workers}")
            return False

        # Validate host
        if not settings.host:
            print("❌ Host cannot be empty")
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

    # Check file permissions using cross-platform method
    sensitive_files = [".env.production", ".env.development"]
    for file in sensitive_files:
        if os.path.exists(file):
            is_secure, message = check_file_permissions(file)
            if not is_secure:
                print(f"⚠️  Warning: {file} has loose permissions")
                print(f"   Details: {message}")
                if platform.system() != "Windows":
                    print(f"   Run: chmod 600 {file}")
                else:
                    print(f"   Consider restricting access to this file")
            else:
                print(f"✅ {file} permissions: {message}")

    # Check for debug mode
    from dotenv import load_dotenv

    load_dotenv(".env.production")

    if os.getenv("DEBUG", "false").lower() == "true":
        print("⚠️  Warning: DEBUG=True in production environment")

    if os.getenv("ENVIRONMENT") != "production":
        print("⚠️  Warning: ENVIRONMENT is not set to 'production'")

    # Display platform-specific security recommendations
    recommendations = get_security_recommendations()
    print("\n".join(recommendations))

    print("✅ Security checks completed")


def start_server():
    """Start the production server"""
    print("🚀 Starting production server...")

    # Set environment
    os.environ["ENVIRONMENT"] = "production"

    # Load configuration settings
    from config import settings

    # Get configuration values
    host = settings.host
    port = str(settings.port)
    workers = str(settings.workers)

    print(f"📋 Server configuration:")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Workers: {workers}")
    print(f"   Environment: {settings.environment}")

    # Start with uvicorn
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        host,
        "--port",
        port,
        "--workers",
        workers,
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
