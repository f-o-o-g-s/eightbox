"""Backup script for creating Git and ZIP backups.

This script handles:
1. Running pre-commit hooks
2. Creating Git commits
3. Creating ZIP backups
4. Handling errors and retries
"""

import argparse
import os
import subprocess
import zipfile
from datetime import datetime

# Constants
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(PROJECT_DIR, "backups")

# Important directories that must be included
IMPORTANT_DIRS = {
    "database",  # Database-related modules
    "tabs",  # Tab-related modules
}

# Important files that must be included
IMPORTANT_FILES = {
    "exclusion_periods.json",  # Exclusion periods configuration
    "carrier_list.json",  # Carrier list configuration
    "app_settings.json",  # Application settings
}

# Directories to exclude from backups
EXCLUDE_DIRS = {
    ".git",
    "backups",
    "__pycache__",
    ".pytest_cache",
    "output",
    ".venv",
    "spreadsheets",
    "node_modules",
    ".idea",
    ".vscode",
}

# File extensions to exclude from backups
EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".zip",
    ".log",
    ".tmp",
    ".temp",
    ".bak",
    ".swp",
    ".swo",
}


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
    """Create a ZIP backup of the source directory.

    Handles file filtering and exclusions based on predefined rules.
    Maintains directory structure in the ZIP file.
    """
    try:
        print("\nCreating ZIP backup...")

        # Create backup directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = os.path.join(target_dir, f"backup_{timestamp}.zip")

        print("Copying files...")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                # Get relative path for current directory
                rel_path = os.path.relpath(root, source_dir)
                path_parts = rel_path.split(os.sep)

                # Skip excluded directories unless they're part of important directories
                if any(excl in path_parts for excl in EXCLUDE_DIRS):
                    # Check if this is a subdirectory of an important directory
                    if not any(imp in path_parts for imp in IMPORTANT_DIRS):
                        continue

                # Filter out excluded directories for next iteration
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

                for file in files:
                    # Always include important files
                    if file in IMPORTANT_FILES:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, source_dir)
                        print(f"Adding: {arcname}")
                        zipf.write(file_path, arcname)
                        continue

                    # Skip excluded file extensions
                    if not any(file.endswith(ext) for ext in EXCLUDE_EXTENSIONS):
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
    """Handle Git version control backup.

    This function handles Git operations including staging changes,
    committing with a timestamped message, and pushing to the target branch.
    The commit message will be prefixed with one of: Fix:, Feature:, or Breaking:
    If no prefix is provided, 'Fix:' will be used as default.
    """
    try:
        # Define valid prefixes
        valid_prefixes = ["Fix:", "Feature:", "Breaking:"]

        # Check if description starts with a valid prefix
        has_valid_prefix = any(
            description.startswith(prefix) for prefix in valid_prefixes
        )

        # If no valid prefix, add 'Fix:' as default
        if not has_valid_prefix:
            description = f"Fix: {description}"

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


def create_backup(cli_description=None, cli_backup_type=None):
    """Create a backup of the project using Git version control.

    Args:
        cli_description (str, optional): Description provided via command line
        cli_backup_type (str, optional): Backup type provided via command line
            (1=Git, 2=ZIP, 3=Both)
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

        # Use provided backup type or show interactive menu
        backup_type = cli_backup_type
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
    parser = argparse.ArgumentParser(description="Create project backups")
    parser.add_argument("description", nargs="?", help="Commit message for the backup")
    parser.add_argument(
        "--zip", action="store_true", help="Create ZIP backup in addition to Git backup"
    )
    args = parser.parse_args()

    if args.description:
        if args.description in ["-h", "--help", "help"]:
            parser.print_help()
        else:
            # Set backup_type based on --zip flag
            backup_type = "3" if args.zip else "1"
            create_backup(args.description, backup_type)
    else:
        create_backup()
