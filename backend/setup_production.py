#!/usr/bin/env python3
"""
Secure Setup Script for StudyMate Production Environment

This script generates secure passwords and provides deployment instructions.
Run this script before deploying to production.
"""

import os
import secrets
import string
import shutil
from pathlib import Path
from typing import Dict


def generate_secure_password(length: int = 32) -> str:
    """Generate a cryptographically secure password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = "".join(secrets.choice(alphabet) for _ in range(length))
    return password


def generate_api_key(length: int = 64) -> str:
    """Generate a secure API key."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_production_env() -> Dict[str, str]:
    """Create production environment variables with secure values."""
    secrets_generated = {}

    # Generate secure passwords
    secrets_generated["POSTGRES_PASSWORD"] = generate_secure_password(32)
    secrets_generated["REDIS_PASSWORD"] = generate_secure_password(32)
    secrets_generated["API_KEY"] = generate_api_key(64)

    return secrets_generated


def backup_existing_env() -> None:
    """Backup existing .env.production file."""
    env_file = Path(".env.production")
    if env_file.exists():
        backup_file = Path(".env.production.backup")
        shutil.copy2(env_file, backup_file)
        print(f"✓ Backed up existing .env.production to {backup_file}")


def update_env_file(secrets: Dict[str, str]) -> None:
    """Update .env.production with secure values."""
    env_file = Path(".env.production")

    if not env_file.exists():
        print("❌ .env.production file not found!")
        return

    content = env_file.read_text()

    # Replace placeholder values with secure ones
    replacements = {
        "CHANGE_ME_SECURE_DB_PASSWORD_FOR_PRODUCTION": secrets["POSTGRES_PASSWORD"],
        "CHANGE_ME_SECURE_REDIS_PASSWORD_FOR_PRODUCTION": secrets["REDIS_PASSWORD"],
        "CHANGE_ME_SECURE_API_KEY_FOR_PRODUCTION": secrets["API_KEY"],
        "CHANGE_ME_DB_PASSWORD": secrets["POSTGRES_PASSWORD"],
    }

    for placeholder, secure_value in replacements.items():
        content = content.replace(placeholder, secure_value)

    env_file.write_text(content)
    print("✓ Updated .env.production with secure values")


def create_env_secrets_file(secrets: Dict[str, str]) -> None:
    """Create a separate secrets file for manual reference."""
    secrets_file = Path(".env.secrets")

    content = f"""# Generated Secure Secrets for StudyMate Production
# KEEP THIS FILE SECURE - DO NOT COMMIT TO VERSION CONTROL
# Generated on: {os.getcwd()}

# Database Password
POSTGRES_PASSWORD={secrets['POSTGRES_PASSWORD']}

# Redis Password  
REDIS_PASSWORD={secrets['REDIS_PASSWORD']}

# API Key
API_KEY={secrets['API_KEY']}

# Instructions:
# 1. These values have been automatically applied to .env.production
# 2. Store these securely in your password manager
# 3. Delete this file after storing the secrets securely
# 4. Never commit this file to version control
"""

    secrets_file.write_text(content)
    print(f"✓ Created {secrets_file} with generated secrets")


def print_deployment_checklist() -> None:
    """Print deployment security checklist."""
    print("\n" + "=" * 60)
    print("PRODUCTION DEPLOYMENT SECURITY CHECKLIST")
    print("=" * 60)
    print("\n📋 REQUIRED ACTIONS:")
    print("1. ✅ Secure passwords generated and applied")
    print("2. 🔄 Update ALLOWED_ORIGINS in .env.production with your domain")
    print("3. 🔄 Update TRUSTED_HOSTS in .env.production with your domain")
    print("4. 🔄 Set your OpenAI API key in .env.production")
    print("5. 🔄 Configure SSL certificates in ./ssl/ directory")
    print("6. 🔄 Review and customize nginx.conf for your domain")
    print("7. 🔄 Set up backup strategy for PostgreSQL database")
    print("8. 🔄 Configure monitoring and alerting")
    print("9. 🔄 Test all endpoints with production configuration")
    print("10. 🔄 Run security audit: python security_audit.py")

    print("\n🚨 SECURITY REMINDERS:")
    print("- Never commit .env.production to version control")
    print("- Use environment variables on production servers")
    print("- Enable firewall and restrict database access")
    print("- Regularly update dependencies and base images")
    print("- Monitor logs for security incidents")
    print("- Use HTTPS only in production")

    print("\n🚀 DEPLOYMENT COMMANDS:")
    print("# Build and start services:")
    print("docker-compose up -d --build")
    print("")
    print("# Check service status:")
    print("docker-compose ps")
    print("")
    print("# View logs:")
    print("docker-compose logs -f studymate-api")
    print("")
    print("# Run security audit:")
    print("python security_audit.py")

    print("\n" + "=" * 60)


def main():
    """Main setup function."""
    print("🔐 StudyMate Production Security Setup")
    print("=" * 40)

    # Check if we're in the right directory
    if not Path(".env.production").exists():
        print("❌ Error: .env.production not found!")
        print("Please run this script from the backend directory.")
        return

    # Generate secure secrets
    print("\n🔑 Generating secure secrets...")
    secrets = create_production_env()

    # Backup existing file
    backup_existing_env()

    # Update environment file
    update_env_file(secrets)

    # Create secrets reference file
    create_env_secrets_file(secrets)

    # Print deployment checklist
    print_deployment_checklist()

    print("\n✅ Production environment setup complete!")
    print("🔒 Store the generated secrets securely and delete .env.secrets")


if __name__ == "__main__":
    main()
