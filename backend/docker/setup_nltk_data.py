#!/usr/bin/env python3
"""
NLTK Data Setup Script

This script downloads required NLTK data packages to avoid runtime downloads
and eliminate the need for SSL certificate verification bypass.

Usage:
    python setup_nltk_data.py

This should be run during the deployment/setup phase to pre-download
all required NLTK resources.
"""

import os
import sys
import time


def _download_package(nltk, package: str, nltk_data_dir: str, get_package_path, max_attempts: int = 4) -> bool:
    """Download one NLTK resource with retries (handles transient CDN / network blips)."""
    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            try:
                nltk.download(
                    package,
                    quiet=True,
                    download_dir=nltk_data_dir,
                    halt_on_error=False,
                )
            except TypeError:
                nltk.download(package, quiet=True, download_dir=nltk_data_dir)
            package_path = get_package_path(package)
            nltk.data.find(package_path)
            return True
        except Exception as e:
            last_err = e
            if attempt < max_attempts:
                time.sleep(1.5 * attempt)
    if last_err:
        print(f"❌ Failed to download {package} after {max_attempts} attempts: {last_err}")
    return False


def download_nltk_data():
    """
    Download required NLTK data packages.

    Uses the NLTK_DATA environment variable if set, otherwise defaults to ~/nltk_data.
    This ensures compatibility with containerized environments where the home directory
    may not be writable.
    """

    def get_package_path(package):
        """
        Determine the correct NLTK data path for a given package.

        Args:
            package (str): The NLTK package name

        Returns:
            str: The path to search for the package
        """
        if "punkt" in package:
            return f"tokenizers/{package}"
        elif package in ["stopwords", "wordnet", "omw-1.4"]:
            return f"corpora/{package}"
        else:
            return f"taggers/{package}"

    try:
        import nltk

        print("📦 Setting up NLTK data...")

        # Set NLTK data path - check environment variable first, then fall back to default
        nltk_data_dir = os.environ.get("NLTK_DATA")
        if nltk_data_dir:
            print(f"🔧 Using NLTK_DATA environment variable: {nltk_data_dir}")
        else:
            nltk_data_dir = os.path.join(os.path.expanduser("~"), "nltk_data")
            print(f"🔧 Using default NLTK data directory: {nltk_data_dir}")

        try:
            os.makedirs(nltk_data_dir, exist_ok=True)
            nltk.data.path = [nltk_data_dir]
        except PermissionError:
            print(f"❌ Permission denied creating directory: {nltk_data_dir}")
            print(
                "💡 Try setting NLTK_DATA environment variable to a writable location"
            )
            return False
        except Exception as e:
            print(f"❌ Error creating NLTK data directory: {e}")
            return False

        # Required NLTK data packages
        required_packages = [
            "punkt",  # Sentence tokenizer
            "stopwords",  # Stop words corpus
            "wordnet",  # WordNet lexical database
            "averaged_perceptron_tagger",  # POS tagger
            "punkt_tab",  # Punkt tokenizer (newer version)
            "omw-1.4",  # Open Multilingual Wordnet
        ]

        downloaded = []
        failed = []

        for package in required_packages:
            if _download_package(nltk, package, nltk_data_dir, get_package_path):
                downloaded.append(package)
                print(f"✓ Downloaded: {package}")
            else:
                failed.append(package)

        print(f"\n📊 NLTK Data Setup Summary:")
        print(f"   Successfully processed: {len(downloaded)} packages")
        if failed:
            print(f"   Failed: {len(failed)} packages - {', '.join(failed)}")

        print(f"   Data location: {nltk_data_dir}")

        # Verify downloads
        print("\n🔍 Verifying downloads...")
        missing = []
        for package in required_packages:
            try:
                package_path = get_package_path(package)
                nltk.data.find(package_path)
                print(f"✓ Verified: {package}")
            except LookupError:
                missing.append(package)
                print(f"❌ Missing: {package}")

        if missing:
            print(
                f"\n⚠️  Warning: {len(missing)} packages are missing and may cause runtime issues."
            )
            return False
        else:
            print("\n✅ All NLTK data packages are available!")
            return True

    except ImportError:
        print("❌ NLTK is not installed. Install it with: pip install nltk")
        return False
    except Exception as e:
        print(f"❌ Error setting up NLTK data: {e}")
        return False


def main():
    """Main function."""
    print("🔧 NLTK Data Setup for StudyMate")
    print("=" * 40)

    success = download_nltk_data()

    if success:
        print("\n✅ NLTK data setup completed successfully!")
        print("🔒 Runtime NLTK downloads and SSL bypass are no longer needed.")
        sys.exit(0)
    else:
        print("\n❌ NLTK data setup failed!")
        print("⚠️  Some packages may need to be downloaded at runtime.")
        sys.exit(1)


if __name__ == "__main__":
    main()
