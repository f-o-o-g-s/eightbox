"""Release build script for Eightbox.

This script automates the process of:
1. Running the PyInstaller build
2. Creating a versioned ZIP file for distribution
3. Cleaning up old build files
"""

import os
import shutil
import subprocess
from datetime import datetime


def get_version():
    """Get current version from eightbox.py."""
    with open("eightbox.py", "r", encoding="utf-8") as f:
        content = f.read()
        import re

        match = re.search(r'VERSION = "([^"]+)"', content)
        if match:
            return match.group(1)
    return datetime.now().strftime("%Y.%m.%d")  # Fallback version


def clean_old_builds():
    """Remove old build and dist directories."""
    print("Cleaning old builds...")
    paths = ["build", "dist"]
    for path in paths:
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"Removed {path}/")


def run_build():
    """Run the PyInstaller build process."""
    print("Running build process...")
    # Get the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    build_bat = os.path.join(script_dir, "build.bat")

    # Run build.bat with shell=True for Windows
    result = subprocess.run([build_bat], shell=True, check=True)
    if result.returncode != 0:
        raise Exception("Build failed!")


def create_distribution_zip():
    """Create ZIP file for distribution."""
    version = get_version()
    zip_name = f"eightbox-{version}-windows"

    print(f"Creating distribution ZIP: {zip_name}.zip")

    # Create ZIP file
    shutil.make_archive(zip_name, "zip", "dist/eightbox")

    print(f"ZIP file created: {zip_name}.zip")
    return f"{zip_name}.zip"


def main():
    """Main build and distribution process."""
    try:
        print("Starting release build process...")

        # Clean old builds
        clean_old_builds()

        # Run build
        run_build()

        # Create distribution ZIP
        zip_file = create_distribution_zip()

        print("\nBuild and packaging complete!")
        print(f"Distribution file: {zip_file}")
        print("\nYou can now upload this file to GitHub releases.")

    except Exception as e:
        print(f"Error during build process: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
