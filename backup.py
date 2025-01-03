"""Backup utility for the Eightbox project.

This module provides functionality for both ZIP and Git backups of the project.
It includes pre-commit hook integration for code quality checks before commits.

Commit Message Format:
    The script enforces conventional commit format:
    <type>: <description>

    Types:
    - feat: A new feature
    - fix: A bug fix
    - docs: Documentation changes
    - style: Code style/formatting changes
    - refactor: Code changes that neither fix a bug nor add a feature
    - perf: Performance improvements
    - test: Adding or fixing tests
    - build: Build system changes
    - ci: CI configuration changes
    - chore: Other changes that don't modify src or test files
    - revert: Reverting previous changes

    Breaking Changes:
    Add ! after type for breaking changes: feat!: description

    Scopes (optional):
    Add scope in parentheses: feat(ui): description

Pre-commit Hooks:
    The following checks are run before each commit:
    - isort: sorts Python imports
    - black: formats Python code
    - flake8: checks code style and quality
    - conventional-pre-commit: enforces commit message format

Usage:
    python backup.py "description"  # Will add "fix:" prefix by default
    python backup.py "feat: new feature"
    python backup.py "fix(ui): bug in carrier list"
    python backup.py "feat!: breaking change"
"""

# Test

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

# Conventional commit types
COMMIT_TYPES = [
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
]


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


def format_conventional_commit(description):
    """Format message to follow conventional commit standards.

    Args:
        description (str): The commit message

    Returns:
        str: Properly formatted conventional commit message
    """
    # If message already follows convention, return as is
    if any(
        description.startswith(f"{t}:")
        or description.startswith(f"{t}!:")
        or description.startswith(f"{t}(")
        for t in COMMIT_TYPES
    ):
        return description

    # Default to fix: prefix
    return f"fix: {description}"


def git_backup(description, target_branch="main"):
    """Handle Git version control backup.

    This function handles Git operations including staging changes,
    committing with a timestamped message, and pushing to the target branch.
    The commit message will follow conventional commit format.
    If no type prefix is provided, 'fix:' will be used as default.

    Returns:
        tuple: (success, had_changes) - Whether the operation succeeded and if there were changes
    """
    try:
        # Format commit message to follow conventional format
        description = format_conventional_commit(description)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        message = f"{description} ({timestamp})"

        # Check for changes
        status = subprocess.run(
            ["git", "status", "--porcelain"], check=True, capture_output=True, text=True
        ).stdout.strip()

        if not status:
            print("\nNo changes to commit in Git.")
            return True, False

        # Git commands
        subprocess.run(["git", "add", "-u"], check=True)
        subprocess.run(["git", "commit", "-m", message], check=True)
        subprocess.run(["git", "push", "origin", target_branch], check=True)

        return True, True

    except subprocess.CalledProcessError as e:
        print(f"\nGit operation failed: {str(e)}")
        return False, False


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
            print(
                "\nEnter a description of your changes (format: <type>: <description>):"
            )
            print(
                "Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert"
            )
            print("Example: fix: correct OTDL excusal handling")
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
        had_git_changes = False
        had_zip_backup = False

        if backup_type in ["1", "3"]:
            git_success, had_changes = git_backup(description, target_branch)
            success &= git_success
            had_git_changes = had_changes

        if backup_type in ["2", "3"]:
            zip_path = create_zip_backup(PROJECT_DIR, BACKUP_DIR)
            had_zip_backup = bool(zip_path)
            success &= had_zip_backup

        if success:
            messages = []
            if had_git_changes:
                messages.append(
                    f"Changes successfully pushed to {target_branch} branch"
                )
            elif backup_type in ["1", "3"]:
                messages.append("No changes to commit in Git")

            if had_zip_backup:
                messages.append("ZIP backup created successfully")

            print("\n" + "\n".join(messages) + "!")
        else:
            print("\nSome backup operations failed. Please check the logs above.")

    except KeyboardInterrupt:
        print("\nBackup cancelled.")
    except (subprocess.CalledProcessError, OSError) as e:
        print(f"\nError: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Create project backups with conventional commit messages.

Examples:
    python backup.py "description"          # Will add "fix:" prefix by default
    python backup.py "feat: new feature"    # For new features
    python backup.py "fix(ui): bug fix"     # With scope
    python backup.py "feat!: breaking"      # Breaking change

Commit Types:
    feat:     A new feature
    fix:      A bug fix
    docs:     Documentation changes
    style:    Code style/formatting
    refactor: Code restructuring
    perf:     Performance improvements
    test:     Testing
    build:    Build system changes
    ci:       CI configuration
    chore:    Maintenance
    revert:   Reverting changes

Optional Formats:
    Breaking changes: Add ! after type (feat!:)
    Scopes: Add in parentheses (fix(ui):)""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "description", nargs="?", help="Commit message (format: <type>: <description>)"
    )
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
