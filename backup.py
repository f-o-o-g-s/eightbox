import subprocess
from datetime import datetime


def create_backup():
    """Create a backup of the current state."""
    try:
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Get description from user
        print("\nWhat changes are you about to make?")
        description = input("Description: ").strip()

        # Create backup commit message
        message = f"BACKUP ({timestamp}): {description}"

        # Git commands
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", message])
        subprocess.run(["git", "push", "origin", "main"])

        print("\nBackup created successfully!")
        print(f"Description: {description}")
        print(f"Timestamp: {timestamp}")

    except KeyboardInterrupt:
        print("\nBackup cancelled.")
    except Exception as e:
        print(f"\nError: {str(e)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        print("\nUsage: python backup.py")
        print("Creates a backup of the current project state.")
        print("\nThe script will:")
        print("1. Ask for a description of upcoming changes")
        print("2. Add all changes to Git")
        print("3. Create a commit with timestamp")
        print("4. Push to GitHub")
    else:
        create_backup()
