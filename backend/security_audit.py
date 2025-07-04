#!/usr/bin/env python3
"""
Security Audit Script for StudyMate Backend
This script checks for common security issues in configuration files.
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any


class SecurityAuditor:
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.issues = []
        self.recommendations = []

    def check_docker_compose(self) -> None:
        """Check docker-compose.yml for security issues."""
        docker_compose_path = self.base_path / "docker-compose.yml"
        if not docker_compose_path.exists():
            self.issues.append("docker-compose.yml not found")
            return

        content = docker_compose_path.read_text()

        # Check for hardcoded secrets (improved pattern)
        hardcoded_patterns = [
            r'password\s*[=:]\s*["\'][^"\'$][^"\']*["\']',  # password="literal"
            r'key\s*[=:]\s*["\'][^"\'$][^"\']*["\']',  # key="literal"
            r'secret\s*[=:]\s*["\'][^"\'$][^"\']*["\']',  # secret="literal"
            r'token\s*[=:]\s*["\'][^"\'$][^"\']*["\']',  # token="literal"
            r"password\s*[=:]\s*[^${\s][^\s]*",  # password=literal (no quotes)
            r"key\s*[=:]\s*[^${\s][^\s]*",  # key=literal (no quotes)
            r"secret\s*[=:]\s*[^${\s][^\s]*",  # secret=literal (no quotes)
            r"token\s*[=:]\s*[^${\s][^\s]*",  # token=literal (no quotes)
        ]

        for pattern in hardcoded_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            # Filter out environment variable references
            actual_hardcoded = [
                m for m in matches if "${" not in m and not m.startswith("$")
            ]
            if actual_hardcoded:
                self.issues.append(
                    f"Potential hardcoded secret in docker-compose.yml: {actual_hardcoded}"
                )

        # Check for proper environment variable usage
        env_var_pattern = r"\$\{[^}]+\}"
        env_vars = re.findall(env_var_pattern, content)
        if env_vars:
            print(
                f"✓ Found {len(env_vars)} environment variables in docker-compose.yml"
            )
        else:
            self.issues.append("No environment variables found in docker-compose.yml")

    def check_env_files(self) -> None:
        """Check .env files for security issues."""
        env_files = [".env.development", ".env.production", ".env.example"]

        for env_file in env_files:
            env_path = self.base_path / env_file
            if not env_path.exists():
                self.issues.append(f"{env_file} not found")
                continue

            content = env_path.read_text()

            # Check for placeholder values in production
            if env_file == ".env.production":
                placeholder_patterns = [
                    r"your-.*-here",
                    r"your-.*-password",
                    r"your-.*-key",
                    r"your-.*-secret",
                    r"CHANGE_ME_.*",
                    r"localhost(?!:)",  # localhost but not localhost:port
                    r"127\.0\.0\.1",
                ]

                for pattern in placeholder_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        self.issues.append(
                            f"Placeholder values in {env_file}: {matches}"
                        )

            # Check for weak passwords
            password_lines = [
                line for line in content.split("\n") if "PASSWORD" in line.upper()
            ]
            for line in password_lines:
                if "=" in line:
                    password = line.split("=", 1)[1].strip()
                    if len(password) < 12 and not password.startswith("your-"):
                        self.issues.append(f"Weak password in {env_file}: {line}")

    def check_docker_security(self) -> None:
        """Check Dockerfile for security best practices."""
        dockerfile_path = self.base_path / "Dockerfile"
        if not dockerfile_path.exists():
            self.issues.append("Dockerfile not found")
            return

        content = dockerfile_path.read_text()

        # Check for root user
        if "USER root" in content:
            self.issues.append("Dockerfile uses root user")
        elif "USER " not in content:
            self.recommendations.append("Consider adding a non-root user to Dockerfile")

        # Check for COPY with proper permissions
        if "COPY --chown=" not in content and "COPY" in content:
            self.recommendations.append(
                "Consider using COPY --chown= for better security"
            )

        # Check for health check
        if "HEALTHCHECK" not in content:
            self.recommendations.append("Consider adding HEALTHCHECK to Dockerfile")
        else:
            print("✓ Health check found in Dockerfile")

    def check_config_security(self) -> None:
        """Check config.py for security issues."""
        config_path = self.base_path / "config.py"
        if not config_path.exists():
            self.issues.append("config.py not found")
            return

        content = config_path.read_text()

        # Check for hardcoded secrets
        hardcoded_patterns = [
            r'password\s*=\s*["\'][^"\']*["\']',
            r'key\s*=\s*["\'][^"\']*["\']',
            r'secret\s*=\s*["\'][^"\']*["\']',
        ]

        for pattern in hardcoded_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                self.issues.append(
                    f"Potential hardcoded secret in config.py: {matches}"
                )

        # Check for proper environment variable usage
        if "os.environ" in content or "os.getenv" in content:
            print("✓ Environment variables used in config.py")
        else:
            self.issues.append("No environment variable usage found in config.py")

    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive security report."""
        self.check_docker_compose()
        self.check_env_files()
        self.check_docker_security()
        self.check_config_security()

        return {
            "issues": self.issues,
            "recommendations": self.recommendations,
            "summary": {
                "total_issues": len(self.issues),
                "total_recommendations": len(self.recommendations),
                "status": "FAIL" if self.issues else "PASS",
            },
        }


def main():
    """Run the security audit."""
    auditor = SecurityAuditor()
    report = auditor.generate_report()

    print("\n" + "=" * 50)
    print("STUDYMATE SECURITY AUDIT REPORT")
    print("=" * 50)

    print(f"\nStatus: {report['summary']['status']}")
    print(f"Issues Found: {report['summary']['total_issues']}")
    print(f"Recommendations: {report['summary']['total_recommendations']}")

    if report["issues"]:
        print("\n🚨 SECURITY ISSUES:")
        for i, issue in enumerate(report["issues"], 1):
            print(f"{i}. {issue}")

    if report["recommendations"]:
        print("\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"{i}. {rec}")

    if not report["issues"]:
        print("\n✅ No critical security issues found!")

    print("\n" + "=" * 50)

    # Save report to file
    report_path = Path("security_audit_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Detailed report saved to: {report_path}")


if __name__ == "__main__":
    main()
