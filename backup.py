"""Handles database backup and restore operations for the application."""
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


def create_backup():
    """Create a backup of the current state."""
    try:
        # Run pre-commit hooks first
        if not run_pre_commit():
            return

        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Get description from user
        print("\nWhat changes are you about to make?")
        description = input("Description: ").strip()

        # Create backup commit message
        message = f"BACKUP ({timestamp}): {description}"

        # Git commands - add specific file types and configs
        files_to_backup = [
            "*.py",
            "pyproject.toml",
            ".gitignore",
            "README.md",
            "LICENSE",
            ".flake8",
            ".pre-commit-config.yaml",
        ]

        for file in files_to_backup:
            subprocess.run(["git", "add", file])

        subprocess.run(["git", "commit", "-m", message])
        subprocess.run(["git", "push", "origin", "main"])

        print("\nBackup created successfully!")
        print(f"Description: {description}")
        print(f"Timestamp: {timestamp}")

    except KeyboardInterrupt:
        print("\nBackup cancelled.")
    except Exception as e:
        print(f"\nError: {str(e)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        print("\nUsage: python backup.py")
        print("Creates a backup of the current project state.")
        print("\nThe script will:")
        print("1. Run pre-commit hooks (black, isort, flake8)")
        print("2. Ask for a description of upcoming changes")
        print("3. Add all changes to Git")
        print("4. Create a commit with timestamp")
        print("5. Push to GitHub")
    else:
        create_backup()
