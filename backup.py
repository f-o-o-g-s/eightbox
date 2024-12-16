"""Handles both Git version control and full project directory backups."""
import os
import subprocess
import zipfile
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(PROJECT_DIR, "backups")


def run_pre_commit():
    """Run pre-commit hooks on all files."""
    print("\nRunning pre-commit hooks...")
    max_retries = 3
    current_try = 0

    while current_try < max_retries:
        try:
            result = subprocess.run(
                ["pre-commit", "run", "--all-files"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )

            # If hooks passed successfully
            if result.returncode == 0:
                return True

            print(result.stdout)
            print(result.stderr)

            # If files were modified by formatting hooks (isort, black, etc)
            if (
                "reformatted" in result.stdout
                or "reformatted" in result.stderr
                or "files were modified" in result.stdout
            ):
                current_try += 1
                if current_try < max_retries:
                    print(
                        "\nRetrying after formatting changes "
                        f"(attempt {current_try + 1}/{max_retries})..."
                    )
                    continue

            # If it failed for other reasons
            print("\nPre-commit hooks failed. Please fix the issues and try again.")
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

    print("\nMax retries reached. Please check the remaining issues and try again.")
    return False


def create_zip_backup(source_dir, target_dir):
    """Create a ZIP backup of the project."""
    try:
        print("\nCreating ZIP backup...")

        # Create backup directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = os.path.join(target_dir, f"backup_{timestamp}.zip")

        print("Copying files...")

        # Directories to exclude
        exclude_dirs = {
            ".git",
            "backups",
            "__pycache__",
            ".pytest_cache",
            "output",
            ".venv",
            "spreadsheets",
        }
        # File extensions to exclude
        exclude_extensions = {".pyc", ".pyo", ".pyd", ".zip"}

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if d not in exclude_dirs]

                for file in files:
                    if not any(file.endswith(ext) for ext in exclude_extensions):
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, source_dir)
                        print(f"Adding: {arcname}")
                        zipf.write(file_path, arcname)

        print(f"\nZIP backup created: {zip_path}")
        return zip_path

    except (OSError, zipfile.BadZipFile) as e:
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


def create_backup(cli_description=None):
    """Create a backup of the project using Git version control.

    Args:
        cli_description (str, optional): Description provided via command line
    """
    try:
        # Run pre-commit hooks first
        if not run_pre_commit():
            print("\nPre-commit hooks failed. Please fix the issues and try again.")
            return

        # Get current branch
        current_branch = (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            .decode()
            .strip()
        )

        print(f"\nYou are on branch: {current_branch}")

        # If not on main, ask where to push
        target_branch = "main"
        if current_branch != "main" and cli_description is None:
            print("\nWhere would you like to push your changes?")
            print(f"1. Current branch ({current_branch})")
            print("2. Main branch")
            choice = input("\nEnter choice (1-2): ").strip()

            if choice == "1":
                target_branch = current_branch

        # Get backup description and type
        description = cli_description
        if description is None:
            print("\nEnter a description of your changes:")
            description = input().strip()

        if not description:
            print("\nError: Description cannot be empty")
            return

        # If using CLI, default to Git backup only
        # Otherwise show interactive menu
        backup_type = "1" if cli_description else None
        if backup_type is None:
            print("\nBackup type:")
            print("1. Git backup only")
            print("2. ZIP backup only")
            print("3. Both Git and ZIP backup")
            backup_type = input("\nEnter choice (1-3): ").strip()

        success = True
        if backup_type in ["1", "3"]:
            success &= git_backup(description, target_branch)

        if backup_type in ["2", "3"]:
            zip_path = create_zip_backup(PROJECT_DIR, BACKUP_DIR)
            success &= bool(zip_path)

        if success:
            print(f"\nBackup successfully pushed to {target_branch} branch!")
        else:
            print("\nSome backup operations failed. Please check the logs above.")

    except KeyboardInterrupt:
        print("\nBackup cancelled.")
    except (subprocess.CalledProcessError, OSError) as e:
        print(f"\nError: {str(e)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help", "help"]:
            print("\nUsage: python backup.py [description]")
            print("Creates both Git and ZIP backups of the project.")
            print("\nArguments:")
            print("  description    Commit message for the backup")
            print("                 If provided, will do Git backup only")
            print("\nInteractive mode (no arguments):")
            print("1. Run pre-commit hooks (black, isort, flake8)")
            print("2. Ask for a description of changes")
            print("3. Offer backup options:")
            print("   - Git backup (version control)")
            print("   - ZIP backup (full directory)")
            print("   - Both Git and ZIP")
            print("4. Create selected backups")
            print("\nZIP backups are stored in ~/eightbox_backups/")
        else:
            create_backup(sys.argv[1])
    else:
        create_backup()
