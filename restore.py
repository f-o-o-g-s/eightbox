import subprocess
from datetime import datetime


def show_backups():
    """Show list of available backups."""
    print("\nAvailable Backups:")
    print("-" * 80)
    result = subprocess.run(
        [
            "git",
            "log",
            "--grep=BACKUP",
            "--pretty=format:%h | %ad | %s",
            "--date=format:%Y-%m-%d %H:%M",
        ],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    print("-" * 80)


def create_restore_branch(commit_hash):
    """Create a new branch for restoration."""
    branch_name = f"restore-{datetime.now().strftime('%Y%m%d-%H%M')}"
    subprocess.run(["git", "checkout", "-b", branch_name, commit_hash])
    return branch_name


def restore_backup():
    """Interactive backup restoration."""
    try:
        # Show available backups
        show_backups()

        # Get commit hash from user
        print("\nEnter the commit hash (left column) to restore:")
        commit_hash = input("Hash: ").strip()

        # Ask about restoration type
        print("\nRestore options:")
        print("1. Restore everything (creates new branch)")
        print("2. Restore specific files")
        choice = input("Choose option (1-2): ").strip()

        if choice == "1":
            # Create new branch and restore everything
            branch_name = create_restore_branch(commit_hash)
            print(f"\nCreated new branch: {branch_name}")
            print("All files restored to backup state")

        elif choice == "2":
            # Restore specific files
            print("\nEnter files to restore (empty line to finish):")
            print("Examples: main_gui.py, *.py, folder/*")
            files = []
            while True:
                file = input("File: ").strip()
                if not file:
                    break
                files.append(file)

            for file in files:
                subprocess.run(["git", "checkout", commit_hash, "--", file])
            print("\nSelected files restored from backup")

        print("\nRestore completed!")
        print("\nTo return to latest version:")
        print("  git checkout main")

    except KeyboardInterrupt:
        print("\nRestore cancelled.")
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Make sure the commit hash is correct")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        print("\nUsage: python restore.py")
        print("Interactive tool to restore from backups")
        print("\nThe script will:")
        print("1. Show list of available backups")
        print("2. Let you choose what to restore")
        print("3. Create a safe restoration branch")
    else:
        restore_backup()
