"""Handles both Git version control and full project directory backups."""
import os
import shutil
import subprocess
from datetime import datetime


def run_pre_commit():
    """Run pre-commit hooks on all files."""
    print("\nRunning pre-commit hooks...")
    try:
        subprocess.run(["pre-commit", "run", "--all-files"], check=True)
        return True
    except subprocess.CalledProcessError:
        print("\nPre-commit hooks failed. Please fix the issues and try again.")
        return False


def create_zip_backup(project_dir, backup_dir):
    """Create a ZIP backup of the entire project directory."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    project_name = os.path.basename(project_dir)
    temp_dir = os.path.join(backup_dir, f"temp_{timestamp}")
    backup_path = os.path.join(backup_dir, f"{project_name}_backup_{timestamp}.zip")

    # Directories/files to exclude from ZIP
    exclude = {
        "__pycache__",
        ".git",
        ".pytest_cache",
        ".venv",
        "venv",
        "node_modules",
        ".DS_Store",
        "output",  # Build output directory
        "spreadsheets",  # Generated Excel files
        "dist",  # PyInstaller dist directory
        "build",  # PyInstaller build directory
        ".eggs",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".Python",
        "develop-eggs",
        "downloads",
        "eggs",
        "parts",
        "sdist",
        "var",
        ".env",
    }

    print("\nCreating ZIP backup...")
    try:
        # Create backup directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)

        # Copy files to temporary directory, excluding unwanted paths
        def ignore_patterns(path, names):
            return {n for n in names if n in exclude}

        print("Copying files...")
        shutil.copytree(project_dir, temp_dir, ignore=ignore_patterns)

        # Create ZIP from temporary directory
        print("Creating ZIP archive...")
        shutil.make_archive(backup_path[:-4], "zip", temp_dir)  # Remove .zip extension

        # Clean up temporary directory
        print("Cleaning up temporary files...")
        shutil.rmtree(temp_dir)

        print(f"\nZIP backup created at: {backup_path}")
        print(f"Backup size: {os.path.getsize(backup_path) / (1024*1024):.1f} MB")
        return backup_path
    except Exception as e:
        print(f"\nError creating ZIP backup: {str(e)}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return None


def git_backup(description):
    """Handle Git version control backup."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        message = f"BACKUP ({timestamp}): {description}"

        # Git commands - only add tracked files and respect .gitignore
        subprocess.run(["git", "add", "-u"], check=True)

        # Add any new config files that should be tracked
        config_files = [
            ".gitignore",
            "pyproject.toml",
            "README.md",
            "LICENSE",
            ".flake8",
            ".pre-commit-config.yaml",
        ]
        for file in config_files:
            try:
                subprocess.run(["git", "add", file], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                pass  # Skip if file doesn't exist

        subprocess.run(["git", "commit", "-m", message], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)

        print("\nGit backup completed successfully!")
        print(f"Description: {description}")
        print(f"Timestamp: {timestamp}")
        return True

    except subprocess.CalledProcessError as e:
        if "nothing to commit" in str(e.output):
            print("\nNo changes to commit in Git.")
            return True
        print(f"\nGit backup error: {str(e)}")
        return False


def create_backup():
    """Create both Git and ZIP backups of the project."""
    try:
        # Run pre-commit hooks first
        if not run_pre_commit():
            return

        # Get description from user
        print("\nWhat changes are you backing up?")
        description = input("Description: ").strip()

        # Get backup preferences
        print("\nWhat would you like to backup?")
        print("1. Git only (version control)")
        print("2. ZIP only (full directory)")
        print("3. Both Git and ZIP")
        choice = input("Enter choice (1-3): ").strip()

        # Determine project and backup directories
        project_dir = os.path.dirname(os.path.abspath(__file__))
        backup_dir = os.path.join(os.path.expanduser("~"), "eightbox_backups")

        success = True
        if choice in ["1", "3"]:
            success &= git_backup(description)

        if choice in ["2", "3"]:
            zip_path = create_zip_backup(project_dir, backup_dir)
            success &= bool(zip_path)

        if success:
            print("\nAll requested backup operations completed successfully!")
        else:
            print("\nSome backup operations failed. Please check the logs above.")

    except KeyboardInterrupt:
        print("\nBackup cancelled.")
    except Exception as e:
        print(f"\nError: {str(e)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        print("\nUsage: python backup.py")
        print("Creates both Git and ZIP backups of the project.")
        print("\nThe script will:")
        print("1. Run pre-commit hooks (black, isort, flake8)")
        print("2. Ask for a description of changes")
        print("3. Offer backup options:")
        print("   - Git backup (version control)")
        print("   - ZIP backup (full directory)")
        print("   - Both Git and ZIP")
        print("4. Create selected backups")
        print("\nZIP backups are stored in ~/eightbox_backups/")
    else:
        create_backup()
