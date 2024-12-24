"""Manages database path configuration and validation."""

import os
import sqlite3


class DatabasePathManager:
    """Manages database path operations and validation."""

    def __init__(self, config_path="settings.json"):
        """Initialize the DatabasePathManager.

        Args:
            config_path (str): Path to the settings file (kept for compatibility)
        """
        self.config_path = config_path

    def load_database_path(self):
        """Load database path from default location.

        Returns:
            str: Path to the database file, or None if not found
        """
        # Default path for Klusterbox database
        if os.name == "nt":  # Windows
            default_path = os.path.join(
                os.path.expanduser("~"),
                "Documents",
                ".klusterbox",
                "mandates.sqlite"
            )
            if os.path.exists(default_path) and self.validate_database_path(default_path):
                return default_path
        return None

    def validate_database_path(self, path):
        """Validate that the given path points to a valid SQLite database.

        Args:
            path (str): Path to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not path or not os.path.exists(path):
            return False

        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()

            # Check for required tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            conn.close()

            required_tables = {"rings3", "carriers"}
            return required_tables.issubset(tables)

        except Exception:
            return False
