"""Handles both Git version control and full project directory backups."""
import os
import shutil
import subprocess
from datetime import datetime

project_dir = os.path.dirname(os.path.abspath(__file__))
backup_dir = os.path.join(project_dir, "backups")


def run_pre_commit():
    """Run pre-commit hooks on all files."""
    print("\nRunning pre-commit hooks...")

    try:
        # First attempt - with UTF-8 encoding
        result = subprocess.run(
            ["pre-commit", "run", "--all-files"],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        if result.returncode == 0:
            return True

        # If failed, check if it was just formatting
        if "reformatted" in result.stdout or "reformatted" in result.stderr:
            print(result.stdout)
            print(result.stderr)

            # Try one more time after reformatting
            print("\nRetrying after reformatting...")
            retry_result = subprocess.run(
                ["pre-commit", "run", "--all-files"],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            return retry_result.returncode == 0

        # If it failed for other reasons, show error and return False
        print("\nPre-commit hooks failed. Please fix the issues and try again.")
        print(result.stdout)
        print(result.stderr)
        return False

    except UnicodeDecodeError:
        # Fallback to running without capturing output
        print("Note: Unable to capture detailed output due to encoding issues.")
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


def git_backup(description, target_branch="main"):
    """Handle Git version control backup."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        message = f"BACKUP ({timestamp}): {description}"

        # Check for changes
        status = subprocess.run(
            ["git", "status", "--porcelain"], check=True, capture_output=True, text=True
        ).stdout.strip()

        if not status:
            print("\nNo changes to commit in Git.")
            return True

        # Git commands
        subprocess.run(["git", "add", "-u"], check=True)
        subprocess.run(["git", "commit", "-m", message], check=True)
        subprocess.run(["git", "push", "origin", target_branch], check=True)
        
        return True

    except subprocess.CalledProcessError as e:
        print(f"\nGit operation failed: {str(e)}")
        return False


def create_backup():
    """Create a backup of the project using Git version control."""
    try:
        # Get current branch
        current_branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        ).decode().strip()
        
        print(f"\nYou are on branch: {current_branch}")
        
        # If not on main, ask where to push
        target_branch = "main"
        if current_branch != "main":
            print("\nWhere would you like to push your changes?")
            print(f"1. Current branch ({current_branch})")
            print("2. Main branch")
            choice = input("\nEnter choice (1-2): ").strip()
            
            if choice == "1":
                target_branch = current_branch
        
        # Get backup description and type
        print("\nEnter a description of your changes:")
        description = input().strip()
        
        if not description:
            print("\nError: Description cannot be empty")
            return

        print("\nBackup type:")
        print("1. Git backup only")
        print("2. ZIP backup only")
        print("3. Both Git and ZIP backup")
        backup_type = input("\nEnter choice (1-3): ").strip()

        success = True
        if backup_type in ["1", "3"]:
            success &= git_backup(description, target_branch)  # Pass target_branch to git_backup

        if backup_type in ["2", "3"]:
            zip_path = create_zip_backup(project_dir, backup_dir)
            success &= bool(zip_path)

        if success:
            print(f"\nBackup successfully pushed to {target_branch} branch!")
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
