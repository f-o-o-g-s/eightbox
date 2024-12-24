"""Module for managing database paths and validation."""

import os
import json
from pathlib import Path
from typing import Optional, Tuple
import sqlite3

from .models import DatabaseError


class DatabasePathManager:
    """Manages database path operations and validation."""
    
    def __init__(self, config_path="settings.json"):
        """Initialize the DatabasePathManager.
        
        Args:
            config_path (str): Path to the settings file
        """
        self.config_path = config_path

    def load_database_path(self):
        """Load database path from settings file or auto-detect.
        
        Returns:
            str: Path to the database file, or None if not found
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    settings = json.load(f)
                    saved_path = settings.get("database_path")
                    if saved_path and os.path.exists(saved_path):
                        if self.validate_database_path(saved_path):
                            return saved_path
        except Exception as e:
            print(f"Error loading settings: {e}")

        # Fall back to auto-detection if loading fails
        return self.auto_detect_klusterbox_path()

    def save_database_path(self, path):
        """Save database path to settings file.
        
        Args:
            path (str): Path to save
        """
        try:
            settings = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    settings = json.load(f)

            settings["database_path"] = path

            with open(self.config_path, "w") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
        return True

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

    def auto_detect_klusterbox_path(self):
        """Auto-detect the Klusterbox database path.
        
        Returns:
            str: Path to mandates.sqlite if found, None otherwise
        """
        if os.name == "nt":  # Windows
            default_path = os.path.expanduser("~") + "\\Documents\\.klusterbox\\mandates.sqlite"
            if os.path.exists(default_path):
                return default_path
        return None 