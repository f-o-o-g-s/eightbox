"""Handles both Git version control and full project directory backups."""
import os
import shutil
import subprocess
from datetime import datetime
import zipfile

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
    """Create a ZIP backup of the project."""
    try:
        print("\nCreating ZIP backup...")
        
        # Create backup directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = os.path.join(backup_dir, f"backup_{timestamp}.zip")
        
        print("Copying files...")
        
        # Directories to exclude
        exclude_dirs = {'.git', 'backups', '__pycache__', '.pytest_cache', 'output', '.venv'}
        # File extensions to exclude
        exclude_extensions = {'.pyc', '.pyo', '.pyd', '.zip'}
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(project_dir):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                
                for file in files:
                    if not any(file.endswith(ext) for ext in exclude_extensions):
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, project_dir)
                        print(f"Adding: {arcname}")  # Show which file is being added
                        zipf.write(file_path, arcname)
        
        print(f"\nZIP backup created: {zip_path}")
        return zip_path
        
    except Exception as e:
        print(f"\nError creating ZIP backup: {str(e)}")
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
