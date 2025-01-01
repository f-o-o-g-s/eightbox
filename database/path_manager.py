"""Manages database path configuration and validation."""

import os
import sqlite3
from pathlib import Path
from PyQt5.QtWidgets import QFileDialog, QApplication
import logging

logger = logging.getLogger(__name__)


class DatabasePathManager:
    """Manages database path operations and validation."""

    def __init__(self):
        """Initialize the DatabasePathManager."""
        pass

    def load_database_path(self):
        """Load database path from possible locations or prompt user.

        Returns:
            str: Path to the database file, or None if not found/selected
        """
        possible_paths = []
        
        if os.name == "nt":  # Windows
            # Check Documents folder (original location)
            docs_path = os.path.join(
                os.path.expanduser("~"), "Documents", ".klusterbox", "mandates.sqlite"
            )
            possible_paths.append(docs_path)
            
            # Check AppData folder (Klusterbox default)
            appdata = os.getenv('APPDATA')
            if appdata:
                appdata_path = os.path.join(appdata, 'Klusterbox', 'mandates.sqlite')
                possible_paths.append(appdata_path)
        else:  # Linux/Unix
            # Check .klusterbox in home directory
            home = str(Path.home())
            linux_path = os.path.join(home, '.klusterbox', 'mandates.sqlite')
            possible_paths.append(linux_path)

        # Try each path until we find a valid database
        for path in possible_paths:
            if os.path.exists(path) and self.validate_database_path(path):
                return path
        
        # If no valid database found, prompt user
        return self.prompt_for_database()

    def prompt_for_database(self):
        """Prompt user to select a database file.

        Returns:
            str: Selected database path if valid, None otherwise
        """
        # Ensure we have a QApplication instance
        if not QApplication.instance():
            QApplication([])

        file_dialog = QFileDialog()
        file_dialog.setWindowTitle("Select Klusterbox Database")
        file_dialog.setNameFilter("SQLite Database (*.sqlite)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)

        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                selected_path = selected_files[0]
                if self.validate_database_path(selected_path):
                    # Ask if user wants to copy to default location
                    target_path = get_klusterbox_db_path()
                    if not os.path.exists(target_path):
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        try:
                            import shutil
                            shutil.copy2(selected_path, target_path)
                            return target_path
                        except Exception:
                            # If copy fails, return original path
                            return selected_path
                    return selected_path
                else:
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.warning(
                        None,
                        "Invalid Database",
                        "The selected file appears to be the main Eightbox database or is not "
                        "a valid mandates database. Please select mandates.sqlite instead."
                    )
        return None

    def validate_database_path(self, path):
        """Validate that the given path points to a valid mandates database."""
        if not path or not os.path.exists(path):
            logger.debug(f"Path does not exist: {path}")
            return False

        try:
            with sqlite3.connect(path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = {row[0] for row in cursor.fetchall()}
                
                logger.debug(f"Found tables: {tables}")
                
                if 'violations' in tables:
                    logger.debug("Rejected: Found violations table")
                    return False
                
                has_mandates = 'mandates' in tables
                has_legacy = 'rings3' in tables and 'carriers' in tables
                
                logger.debug(f"Database validation - Has mandates: {has_mandates}, Has legacy: {has_legacy}")
                
                return has_mandates or has_legacy

        except Exception as e:
            logger.error(f"Database validation error: {e}")
            return False

def get_klusterbox_db_path():
    """Get the path to the Klusterbox database file."""
    if os.name == 'nt':  # Windows
        appdata = os.getenv('APPDATA')
        return os.path.join(appdata, 'Klusterbox', 'mandates.sqlite')
    else:  # Linux
        # Emulate Windows AppData location in Linux home directory
        home = str(Path.home())
        return os.path.join(home, '.klusterbox', 'mandates.sqlite')

def ensure_klusterbox_path_exists():
    """Ensure the Klusterbox database directory exists."""
    db_path = get_klusterbox_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return db_path
