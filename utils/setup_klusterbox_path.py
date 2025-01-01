#!/usr/bin/env python3
import os
import sys
import shutil
from pathlib import Path

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from database.path_manager import get_klusterbox_db_path, ensure_klusterbox_path_exists

def setup_klusterbox_database(source_db_path=None):
    """
    Set up the Klusterbox database in the correct location.
    
    Args:
        source_db_path (str, optional): Path to the source mandates.sqlite file.
            If None, will just create the directory structure.
    """
    target_path = ensure_klusterbox_path_exists()
    
    if source_db_path and os.path.exists(source_db_path):
        shutil.copy2(source_db_path, target_path)
        print(f"Copied database to: {target_path}")
    else:
        print(f"Klusterbox directory created at: {os.path.dirname(target_path)}")
        print(f"Place your mandates.sqlite file at: {target_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Set up Klusterbox database location")
    parser.add_argument("--db", help="Path to source mandates.sqlite file", default=None)
    args = parser.parse_args()
    
    setup_klusterbox_database(args.db) 