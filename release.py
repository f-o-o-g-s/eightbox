import os
import subprocess
from datetime import datetime
from pathlib import Path

from github import Github


def show_help():
    """Show help information about using the release script."""
    help_text = """
    Eightbox Release Script
    ======================

    This script handles version updates and releases for Eightbox.

    Usage:
        python release.py [--help]

    Version Format: YYYY.MAJOR.MINOR.PATCH
        - YYYY:  Current year
        - MAJOR: Breaking changes
        - MINOR: New features
        - PATCH: Bug fixes

    Examples:
        Bug fix release:
            > python release.py
            > Choose: 1 (Patch)
            > Message: "Fix carrier list display bug"
            > Notes:
            - Fixed sorting in carrier list
            - Updated error messages

        New feature release:
            > python release.py
            > Choose: 2 (Minor)
            > Message: "Add new violation detection"
            > Notes:
            - Added automatic violation detection
            - Improved user interface

    Environment:
        GITHUB_TOKEN - GitHub personal access token for releases
                      (Will prompt if not set)

    Note: Token needs 'Contents: Read & write' permission
    """
    print(help_text)


def get_github_token():
    """Get GitHub token from environment or prompt user."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("\nNo GITHUB_TOKEN environment variable found.")
        print("Please create a token at: https://github.com/settings/tokens")
        token = input("Enter your GitHub token: ").strip()
    return token


def format_release_notes(version, notes, commit_msg):
    """Format release notes in a structured way."""
    return f"""# Version {version}

## Overview
{commit_msg}

## What's New
{chr(10).join(notes)}

## Technical Details
- Release Date: {datetime.now().strftime('%Y-%m-%d')}
- Build Time: {datetime.now().strftime('%H:%M')}
- Commit: {subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()[:8]}

[Full Changelog](https://github.com/f-o-o-g-s/eightbox/commits/main)
"""


def get_new_version(current_version, update_type):
    """Get new version number based on update type."""
    year, major, minor, patch = map(int, current_version.split("."))
    current_year = datetime.now().year

    if update_type == "4":  # Year
        return f"{current_year}.0.0.0"
    elif update_type == "3":  # Major - FIXED THIS PART
        if year != current_year:
            return f"{current_year}.0.0.0"
        if major == 0:  # If it's the first major version
            return f"{year}.0.0.0"
        return f"{year}.{major + 1}.0.0"
    elif update_type == "2":  # Minor
        return f"{year}.{major}.{minor + 1}.0"
    else:  # Patch
        return f"{year}.{major}.{minor}.{patch + 1}"


def update_version_and_release():
    try:
        # 1. Get version update type from user
        print("\nWhat type of update is this?")
        print("1. Patch (bug fixes)")
        print("2. Minor (new features)")
        print("3. Major (breaking changes)")
        print("4. Year (new year update)")
        choice = input("Enter choice (1-4): ")

        update_types = {"1": "patch", "2": "minor", "3": "major", "4": "year"}

        if choice not in update_types:
            raise ValueError("Invalid choice")

        # 2. Get commit message
        commit_msg = input("\nEnter commit message: ")

        # 3. Get release notes
        print("\nEnter release notes (one per line, empty line to finish):")
        release_notes = []
        while True:
            note = input("- ")
            if not note:
                break
            release_notes.append(f"- {note}")

        # 4. Update version in main_gui.py
        from main_gui import MainApp

        old_version = MainApp.VERSION
        new_version = get_new_version(old_version, choice)

        # 5. Update build time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        MainApp.BUILD_TIME = current_time

        # 6. Write changes back to file
        main_gui_path = Path("main_gui.py")
        content = main_gui_path.read_text()

        # Update version
        content = content.replace(
            f'VERSION = "{old_version}"', f'VERSION = "{new_version}"'
        )

        # Update build time
        content = content.replace(
            f'BUILD_TIME = "{MainApp.BUILD_TIME}"', f'BUILD_TIME = "{current_time}"'
        )

        main_gui_path.write_text(content)

        # 7. Git commands - Updated order
        subprocess.run(["git", "add", "main_gui.py"], check=True)
        subprocess.run(
            ["git", "commit", "-m", f"{commit_msg} (v{new_version})"], check=True
        )
        subprocess.run(["git", "push", "origin", "main"], check=True)

        # Get the current commit SHA
        commit_sha = (
            subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        )

        # Format release notes with commit SHA
        formatted_notes = format_release_notes(new_version, release_notes, commit_msg)

        # Create tag with formatted notes
        subprocess.run(
            ["git", "tag", "-a", f"v{new_version}", "-m", formatted_notes], check=True
        )
        subprocess.run(["git", "push", "origin", "--tags"], check=True)

        # 8. Create GitHub Release - Updated to use commit SHA
        token = get_github_token()
        g = Github(token)
        repo = g.get_user().get_repo("eightbox")

        # Create release with specific commit
        release = repo.create_git_release(
            tag=f"v{new_version}",
            name=f"Version {new_version}",
            message=formatted_notes,
            draft=False,
            prerelease=False,
            target_commitish=commit_sha,  # Explicitly set the commit
        )

        print(f"\nSuccessfully released version {new_version}!")
        print(f"Release URL: {release.html_url}")
        print(f"Commit SHA: {commit_sha}")

    except subprocess.CalledProcessError as e:
        print(f"\nGit command failed: {e.cmd}")
        print(
            f"Error output: {e.stderr if hasattr(e, 'stderr') else 'No error output'}"
        )
    except Exception as e:
        print(f"\nError: {str(e)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        show_help()
    else:
        try:
            update_version_and_release()
        except KeyboardInterrupt:
            print("\nRelease process cancelled.")
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Use --help to see usage information.")
