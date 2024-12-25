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
    """Create distribution archive using 7-Zip with maximum compression.

    Uses 7-Zip's Ultra compression preset with LZMA2 algorithm and a large dictionary
    size for maximum compression. The -mx=9 flag sets compression to Ultra level.

    Returns:
        str: Path to the created archive file
    """
    version = get_version()
    archive_name = f"eightbox-{version}-windows"
    archive_path = os.path.abspath(f"{archive_name}.7z")
    dist_path = os.path.abspath("dist/eightbox")

    print(f"Creating distribution archive: {archive_path}")

    try:
        # Try to use 7-Zip with maximum compression
        sevenzip_path = "C:/Program Files/7-Zip/7z.exe"
        if not os.path.exists(sevenzip_path):
            sevenzip_path = "C:/Program Files (x86)/7-Zip/7z.exe"

        if os.path.exists(sevenzip_path):
            # Remove existing archive if it exists
            if os.path.exists(archive_path):
                os.remove(archive_path)

            # Use 7-Zip with absolute paths and maximum compression
            subprocess.run(
                [
                    sevenzip_path,
                    "a",  # Add to archive
                    "-t7z",  # 7z format
                    "-m0=lzma2",  # LZMA2 method
                    "-mx=9",  # Ultra compression
                    "-mfb=273",  # Maximum number of fast bytes
                    "-ms=on",  # Solid archive
                    archive_path,  # Output file
                    f"{dist_path}/*",  # Input files
                ],
                check=True,
            )
            print(f"Archive created with 7-Zip compression: {archive_path}")
            return archive_path
        else:
            raise FileNotFoundError("7-Zip not found in Program Files")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(
            f"7-Zip compression failed ({str(e)}), falling back to standard ZIP compression..."
        )
        # Fallback to standard ZIP if 7-Zip is not available
        zip_path = os.path.abspath(f"{archive_name}.zip")
        shutil.make_archive(archive_name, "zip", "dist/eightbox")
        print(f"ZIP file created with standard compression: {zip_path}")
        return zip_path


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
