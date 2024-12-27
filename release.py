"""Release script for Eightbox.

This script handles version management and release creation for Eightbox.
It follows semantic versioning with the format YYYY.MAJOR.MINOR.PATCH.

Interactive Usage:
    python release.py

Non-Interactive Usage:
    python release.py --non-interactive --type TYPE --message MSG --notes NOTE1 NOTE2

Examples:
    # Interactive mode
    python release.py

    # Non-interactive patch release
    python release.py --non-interactive \
        --type patch \
        --message "fix: correct OTDL excusal handling" \
        --notes "Fixed bug in 8.5.G violations" "Updated error messages"

    # Non-interactive minor release
    python release.py --non-interactive \
        --type minor \
        --message "feat: add new carrier filtering" \
        --notes "Added carrier name filtering" "Improved UI responsiveness"

    # Non-interactive major release
    python release.py --non-interactive \
        --type major \
        --message "feat!: redesign violation detection system" \
        --notes "Complete overhaul of violation detection" "Breaking API changes"

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

Release Types:
    - patch: Bug fixes and minor changes (Z in X.Y.Z)
    - minor: New features (Y in X.Y.Z)
    - major: Breaking changes (X in X.Y.Z)

Notes for AI Assistant:
    1. Always use --non-interactive mode for consistency
    2. Match commit type to release type:
       - patch → fix:, docs:, style:, test:
       - minor → feat:
       - major → feat!:
    3. Include relevant scope if known (e.g., fix(85g):)
    4. Notes should be specific and descriptive
    5. For major releases, emphasize breaking changes in notes
"""

import argparse
import os
import re
import subprocess
from datetime import datetime

from github import Github

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


def format_conventional_commit(message, release_type):
    """Format message to follow conventional commit standards.

    Args:
        message (str): The commit message
        release_type (str): The type of release (patch, minor, major)

    Returns:
        str: Properly formatted conventional commit message
    """
    # If message already follows convention, return as is
    if any(
        message.startswith(f"{t}:")
        or message.startswith(f"{t}!:")
        or message.startswith(f"{t}(")
        for t in COMMIT_TYPES
    ):
        return message

    # Auto-prefix based on release type
    if release_type == "major":
        prefix = "feat!"
    elif release_type == "minor":
        prefix = "feat"
    else:  # patch
        prefix = "fix"

    return f"{prefix}: {message}"


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
    """Format release notes in a standardized markdown format.

    Creates a standardized release notes document including:
    - Version number
    - Overview (commit message)
    - What's New (bullet points)
    - Technical details (date, time, commit hash)
    - Link to full changelog

    Also updates:
    - CHANGELOG.md with the new version entry
    - README.md's recent changes section

    Args:
        version (str): Version number in YYYY.MAJOR.MINOR.PATCH format
        notes (list): List of release note bullet points
        commit_msg (str): Main commit message describing the release

    Returns:
        str: Formatted release notes in markdown format

    Note:
        Includes the current git commit hash truncated to 8 characters
    """
    # Format the release notes for GitHub release
    release_notes = f"""# Version {version}

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

    # Update CHANGELOG.md
    changelog_entry = f"""## [{version}] - {datetime.now().strftime('%Y-%m-%d')}
{chr(10).join(notes)}

"""
    try:
        with open("CHANGELOG.md", "r", encoding="utf-8") as f:
            content = f.read()
            # Insert after the first line (# Changelog)
            content = content.split("\n", 2)
            content.insert(1, "\n" + changelog_entry)
            content = "\n".join(content)
        with open("CHANGELOG.md", "w", encoding="utf-8") as f:
            f.write(content)
    except FileNotFoundError:
        # Create new CHANGELOG.md if it doesn't exist
        with open("CHANGELOG.md", "w", encoding="utf-8") as f:
            f.write(
                f"""# Changelog

All notable changes to Eightbox will be documented in this file.

{changelog_entry}"""
            )

    # Update README.md recent changes
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
            # Find the Recent Changes section
            start = content.find("### Recent Changes")
            if start != -1:
                # Create the new version entry
                new_version_entry = f"""### {version}
{chr(10).join(notes)}

"""
                # Get the content before the Recent Changes section
                prefix = content[:start]
                # Add the Recent Changes header and new version
                new_content = prefix + "### Recent Changes\n\n" + new_version_entry
                # Get existing versions and keep only the
                # 2 most recent (since we're adding a new one)
                versions = content[start:].split("### 202")[1:3]
                if versions:
                    new_content += "### " + "### ".join(versions)
                with open("README.md", "w", encoding="utf-8") as f:
                    f.write(new_content)
    except FileNotFoundError:
        print("README.md not found, skipping recent changes update")

    return release_notes


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
    """Get the current version from eightbox.py file."""
    with open("eightbox.py", "r", encoding="utf-8") as f:
        content = f.read()
        match = re.search(r'VERSION = "([^"]+)"', content)
        if match:
            return match.group(1)
        raise ValueError("Could not find VERSION in eightbox.py")


def update_version_and_build_time(version):
    """Update version and build time in eightbox.py file."""
    build_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    with open("eightbox.py", "r", encoding="utf-8") as f:
        content = f.read()

    content = re.sub(r'VERSION = "[^"]+"', f'VERSION = "{version}"', content)
    content = re.sub(r'BUILD_TIME = "[^"]+"', f'BUILD_TIME = "{build_time}"', content)

    with open("eightbox.py", "w", encoding="utf-8") as f:
        f.write(content)


def build_and_package(version):
    """Build the executable and create distribution package.

    Args:
        version (str): Version number for the package name

    Returns:
        str: Path to the created archive file
    """
    try:
        # Import functions from release_build
        from release_build import (
            clean_old_builds,
            create_distribution_zip,
            run_build,
        )

        print("\nBuilding executable and creating distribution package...")

        # Clean old builds
        clean_old_builds()

        # Run build
        run_build()

        # Create distribution archive (7z or ZIP)
        archive_file = create_distribution_zip()

        return archive_file

    except Exception as e:
        print(f"\nError during build process: {str(e)}")
        raise


def upload_release_asset(release, archive_file, max_retries=3, timeout=300):
    """Upload an asset to a GitHub release with retries.

    Args:
        release: GitHub release object
        archive_file (str): Path to the archive file
        max_retries (int): Maximum number of retry attempts
        timeout (int): Timeout in seconds for the upload (currently unused)

    Returns:
        bool: True if upload successful, False otherwise
    """
    if not os.path.exists(archive_file):
        print(f"\nError: Distribution file not found: {archive_file}")
        return False

    content_type = (
        "application/x-7z-compressed"
        if archive_file.endswith(".7z")
        else "application/zip"
    )

    for attempt in range(max_retries):
        try:
            print(
                f"\nUploading distribution package (attempt {attempt + 1}/{max_retries})..."
            )
            release.upload_asset(
                path=archive_file,
                content_type=content_type,
                name=os.path.basename(archive_file),
            )
            print(f"Successfully uploaded: {archive_file}")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Upload failed ({str(e)}), retrying...")
                continue
            else:
                print(f"\nFailed to upload after {max_retries} attempts: {str(e)}")
                return False


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
        release_type = {1: "patch", 2: "minor", 3: "major"}[choice]

        print("\nEnter a short commit message:")
        print("Format: <type>: <description>")
        print(
            "Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert"
        )
        print("Example: feat: add new carrier filtering")
        commit_msg = input().strip()

        if not commit_msg:
            print("\nCommit message cannot be empty")
            return False

        # Format commit message to follow conventional commits
        commit_msg = format_conventional_commit(commit_msg, release_type)

        print("\nEnter release notes (one per line, empty line to finish):")
        release_notes = []
        while True:
            note = input().strip()
            if not note:
                break
            release_notes.append(f"- {note}")

        # 4. Update version and build time
        new_version = get_new_version(old_version, choice)
        update_version_and_build_time(new_version)

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

        # Build and package the application
        archive_file = build_and_package(new_version)

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

        # Upload the distribution archive with retries
        if not upload_release_asset(release, archive_file):
            print("\nWarning: Release created but asset upload failed.")
            print("You can manually upload the distribution file later.")
            print(f"File to upload: {archive_file}")
            print(f"Release URL: {release.html_url}")
        else:
            print(f"\nSuccessfully released version {new_version}!")
            print(f"Release URL: {release.html_url}")
            print(f"Commit SHA: {commit_sha}")
            print("\nRelease Summary:")
            print(f"Type: {release_type}")
            print(f"Version: {new_version}")
            print(f"Commit Message: {commit_msg}")
            print("\nRelease Notes:")
            for note in formatted_notes.split("\n"):
                if note.strip():
                    print(note)

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

        # Format commit message to follow conventional commits
        commit_msg = format_conventional_commit(commit_msg, release_type)

        # Format notes if they're not already formatted
        formatted_notes = []
        for note in notes:
            if not note.startswith("- "):
                note = f"- {note}"
            formatted_notes.append(note)

        # 4. Update version and build time
        new_version = get_new_version(old_version, choice)
        update_version_and_build_time(new_version)

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

        # Build and package the application
        archive_file = build_and_package(new_version)

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

        # Upload the distribution archive with retries
        if not upload_release_asset(release, archive_file):
            print("\nWarning: Release created but asset upload failed.")
            print("You can manually upload the distribution file later.")
            print(f"File to upload: {archive_file}")
            print(f"Release URL: {release.html_url}")
        else:
            print(f"\nSuccessfully released version {new_version}!")
            print(f"Release URL: {release.html_url}")
            print(f"Commit SHA: {commit_sha}")
            print("\nRelease Summary:")
            print(f"Type: {release_type}")
            print(f"Version: {new_version}")
            print(f"Commit Message: {commit_msg}")
            print("\nRelease Notes:")
            for note in formatted_notes.split("\n"):
                if note.strip():
                    print(note)

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
