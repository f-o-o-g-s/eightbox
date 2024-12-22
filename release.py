"""Module for managing application releases and version updates.

This module provides functionality for:
- Version number management (YYYY.MAJOR.MINOR.PATCH format)
- Release notes generation
- Git operations (commits, tags, pushes)
- GitHub release creation
- Build time tracking
"""

import argparse
import os
import re
import subprocess
from datetime import datetime

from github import Github


def show_help():
    """Show help information about using the release script."""
    help_text = """
    Eightbox Release Script
    ======================

    This script handles version updates and releases for Eightbox.

    Usage:
        python release.py [options]
        python release.py --non-interactive --type {patch|minor|major}
        --message "commit message" --notes "note1" "note2" ...

    Version Format: YYYY.MAJOR.MINOR.PATCH
        - YYYY:  Current year
        - MAJOR: Breaking changes
        - MINOR: New features
        - PATCH: Bug fixes

    Examples:
        Interactive mode:
            > python release.py
            > Choose: 1 (Patch)
            > Message: "Fix carrier list display bug"
            > Notes:
            - Fixed sorting in carrier list
            - Updated error messages

        Non-interactive mode:
            > python release.py --non-interactive --type minor \\
                --message "Add new violation detection" \\
                --notes "Added automatic violation detection" \\
                       "Improved user interface"

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
    """Format release notes in a structured markdown format.

    Creates a standardized release notes document including:
    - Version number
    - Overview (commit message)
    - What's New (bullet points)
    - Technical details (date, time, commit hash)
    - Link to full changelog

    Args:
        version (str): Version number in YYYY.MAJOR.MINOR.PATCH format
        notes (list): List of release note bullet points
        commit_msg (str): Main commit message describing the release

    Returns:
        str: Formatted release notes in markdown format

    Note:
        Includes the current git commit hash truncated to 8 characters
    """
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
    """Calculate the new version number based on update type.

    Follows the YYYY.MAJOR.MINOR.PATCH versioning scheme, where:
    - YYYY: Current year (resets other numbers when changed)
    - MAJOR: Increments for breaking changes (resets minor and patch)
    - MINOR: Increments for new features (resets patch)
    - PATCH: Increments for bug fixes

    Args:
        current_version (str): Current version in YYYY.MAJOR.MINOR.PATCH format
        update_type (int): Type of update (1=patch, 2=minor, 3=major)

    Returns:
        str: New version number in YYYY.MAJOR.MINOR.PATCH format

    Note:
        When year changes, all other numbers reset to 0
    """
    year, major, minor, patch = map(int, current_version.split("."))
    current_year = datetime.now().year

    if update_type == 3:  # Major
        if year != current_year:
            return f"{current_year}.0.0.0"
        return f"{year}.{major + 1}.0.0"
    if update_type == 2:  # Minor
        return f"{year}.{major}.{minor + 1}.0"
    # Patch
    return f"{year}.{major}.{minor}.{patch + 1}"


def get_current_version():
    """Get the current version from main_gui.py file."""
    with open("main_gui.py", "r", encoding="utf-8") as f:
        content = f.read()
        version_match = re.search(r'VERSION = "([^"]+)"', content)
        if version_match:
            return version_match.group(1)
        raise ValueError("Could not find VERSION in main_gui.py")


def update_version_and_time(old_version, new_version):
    """Update version and build time in main_gui.py file."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    with open("main_gui.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Update version
    content = content.replace(
        f'VERSION = "{old_version}"', f'VERSION = "{new_version}"'
    )

    # Update build time using regex to handle any existing time
    content = re.sub(r'BUILD_TIME = "[^"]+"', f'BUILD_TIME = "{current_time}"', content)

    with open("main_gui.py", "w", encoding="utf-8") as f:
        f.write(content)

    return current_time


def create_release():
    """Create a new release with version bump and release notes."""
    try:
        # 1. Get current version
        old_version = get_current_version()

        # 2-3. Get release type and notes
        print("\nWhat type of release is this?")
        print("1. Patch (bug fixes)")
        print("2. Minor (new features)")
        print("3. Major (breaking changes)")
        choice = input("\nEnter choice (1-3): ").strip()

        if not choice or choice not in "123":
            print("\nInvalid choice. Please enter 1, 2, or 3.")
            return False

        choice = int(choice)  # Convert to integer for version calculation

        print("\nEnter a short commit message:")
        commit_msg = input().strip()

        if not commit_msg:
            print("\nCommit message cannot be empty")
            return False

        print("\nEnter release notes (one per line, empty line to finish):")
        release_notes = []
        while True:
            note = input().strip()
            if not note:
                break
            release_notes.append(f"- {note}")

        # 4. Update version and build time
        new_version = get_new_version(old_version, choice)
        update_version_and_time(old_version, new_version)

        # 5. Git commands - now adding all changes
        subprocess.run(["git", "add", "."], check=True)
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

        # 6. Create GitHub Release
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
            target_commitish=commit_sha,
        )

        print(f"\nSuccessfully released version {new_version}!")
        print(f"Release URL: {release.html_url}")
        print(f"Commit SHA: {commit_sha}")

        return True

    except subprocess.CalledProcessError as e:
        print(f"\nGit command failed: {e.cmd}")
        print(
            f"Error output: {e.stderr if hasattr(e, 'stderr') else 'No error output'}"
        )
        return False

    except Exception as e:
        print(f"\nError: {str(e)}")
        return False


def create_release_non_interactive(release_type, commit_msg, notes):
    """Create a new release with provided parameters without user interaction."""
    try:
        # 1. Get current version
        old_version = get_current_version()

        # Convert release type to choice number
        type_map = {"patch": 1, "minor": 2, "major": 3}
        choice = type_map[release_type.lower()]

        # Format notes if they're not already formatted
        formatted_notes = []
        for note in notes:
            if not note.startswith("- "):
                note = f"- {note}"
            formatted_notes.append(note)

        # 4. Update version and build time
        new_version = get_new_version(old_version, choice)
        update_version_and_time(old_version, new_version)

        # 5. Git commands - now adding all changes
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(
            ["git", "commit", "-m", f"{commit_msg} (v{new_version})"], check=True
        )
        subprocess.run(["git", "push", "origin", "main"], check=True)

        # Get the current commit SHA
        commit_sha = (
            subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        )

        # Format release notes with commit SHA
        formatted_notes = format_release_notes(new_version, formatted_notes, commit_msg)

        # Create tag with formatted notes
        subprocess.run(
            ["git", "tag", "-a", f"v{new_version}", "-m", formatted_notes], check=True
        )
        subprocess.run(["git", "push", "origin", "--tags"], check=True)

        # 6. Create GitHub Release
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
            target_commitish=commit_sha,
        )

        print(f"\nSuccessfully released version {new_version}!")
        print(f"Release URL: {release.html_url}")
        print(f"Commit SHA: {commit_sha}")

        return True

    except subprocess.CalledProcessError as e:
        print(f"\nGit command failed: {e.cmd}")
        print(
            f"Error output: {e.stderr if hasattr(e, 'stderr') else 'No error output'}"
        )
        return False

    except Exception as e:
        print(f"\nError: {str(e)}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Eightbox Release Script")
    parser.add_argument(
        "--non-interactive", action="store_true", help="Run in non-interactive mode"
    )
    parser.add_argument(
        "--type", choices=["patch", "minor", "major"], help="Release type"
    )
    parser.add_argument("--message", "-m", help="Commit message")
    parser.add_argument("--notes", nargs="+", help="Release notes (multiple arguments)")

    args = parser.parse_args()

    if args.non_interactive:
        if not all([args.type, args.message, args.notes]):
            print(
                "Error: When using --non-interactive, "
                "you must provide --type, --message, and --notes"
            )
            parser.print_help()
            exit(1)
        create_release_non_interactive(args.type, args.message, args.notes)
    else:
        create_release()
