"""Git restoration utilities for the application.

This module provides functions for restoring files to previous states,
working alongside backup.py and release.py to provide a complete
version control workflow.
"""

import subprocess
from datetime import datetime

from custom_widgets import (
    CustomErrorDialog,
    CustomMessageBox,
)


def restore_to_backup(main_window, backup_description=None):
    """Restore to a specific backup commit.

    Args:
        main_window: Main application window for displaying dialogs
        backup_description: Optional description to find specific backup
    """
    try:
        # Find backup commits
        if backup_description:
            cmd = [
                "git",
                "log",
                "--grep=BACKUP",
                f"--grep={backup_description}",
                "--format=%H|%s",
                "-i",
            ]  # -i for case-insensitive
        else:
            cmd = ["git", "log", "--grep=BACKUP", "--format=%H|%s"]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        commits = result.stdout.strip().split("\n")

        if not commits or not commits[0]:
            raise Exception("No backup commits found")

        # If multiple backups found, let user choose
        if len(commits) > 1:
            print("\nAvailable backups:")
            for i, commit in enumerate(commits, 1):
                hash, msg = commit.split("|")
                print(f"{i}. {msg} ({hash[:8]})")

            choice = input(
                "\nEnter backup number to restore (or press Enter for latest): "
            )
            if choice.strip():
                commit_hash = commits[int(choice) - 1].split("|")[0]
            else:
                commit_hash = commits[0].split("|")[0]
        else:
            commit_hash = commits[0].split("|")[0]

        # Create a new backup before restoring
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        subprocess.run(["git", "add", "-u"], check=True)
        subprocess.run(
            ["git", "commit", "-m", f"BACKUP ({timestamp}): Before restore operation"],
            check=True,
        )

        # Restore to the selected commit
        subprocess.run(["git", "checkout", commit_hash], check=True)

        CustomMessageBox.information(
            main_window,
            "Restore Successful",
            f"Files have been restored to backup commit {commit_hash[:8]}\n"
            f"A backup of your previous state was created at {timestamp}",
        )

    except Exception as e:
        CustomErrorDialog.error(
            main_window, "Restore Failed", f"Failed to restore from backup: {str(e)}"
        )


def restore_to_version(main_window, version=None):
    """Restore to a specific version release.

    Args:
        main_window: Main application window for displaying dialogs
        version: Optional specific version to restore to
    """
    try:
        # Get list of version tags
        result = subprocess.run(
            ["git", "tag", "-l", "v*", "--sort=-v:refname"],
            capture_output=True,
            text=True,
            check=True,
        )
        versions = result.stdout.strip().split("\n")

        if not versions or not versions[0]:
            raise Exception("No version releases found")

        # If version not specified, show list
        if not version:
            print("\nAvailable versions:")
            for i, ver in enumerate(versions, 1):
                # Get commit message for this tag
                msg = subprocess.run(
                    ["git", "tag", "-l", "--format=%(contents)", ver],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                print(f"{i}. {ver} - {msg.stdout.split('\n')[0]}")

            choice = input(
                "\nEnter version number to restore (or press Enter for latest): "
            )
            if choice.strip():
                version_tag = versions[int(choice) - 1]
            else:
                version_tag = versions[0]
        else:
            version_tag = f"v{version}"
            if version_tag not in versions:
                raise Exception(f"Version {version} not found")

        # Create a new backup before restoring
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        subprocess.run(["git", "add", "-u"], check=True)
        subprocess.run(
            ["git", "commit", "-m", f"RELEASE ({timestamp}): Before restore operation"],
            check=True,
        )

        # Restore to the selected commit
        subprocess.run(["git", "checkout", version_tag], check=True)

        CustomMessageBox.information(
            main_window,
            "Restore Successful",
            f"Files have been restored to release version {version_tag}\n"
            f"A backup of your previous state was created at {timestamp}",
        )

    except Exception as e:
        CustomErrorDialog.error(
            main_window, "Restore Failed", f"Failed to restore to version: {str(e)}"
        )
