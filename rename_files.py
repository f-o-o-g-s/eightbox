import os
import re
from pathlib import Path

# Define the file mappings (old_name -> new_name)
file_mappings = {
    'vio_85D_tab.py': 'violation_85d_tab.py',
    'vio_85F_tab.py': 'violation_85f_tab.py',
    'vio_85F_ns_tab.py': 'violation_85f_ns_tab.py',
    'vio_85F_5th_tab.py': 'violation_85f_5th_tab.py',
    'vio_MAX12_tab.py': 'violation_max12_tab.py',
    'vio_MAX60_tab.py': 'violation_max60_tab.py'
}

# Define class mappings (old_name -> new_name)
class_mappings = {
    'Violation85DTab': 'Violation85dTab',
    'Violation85FTab': 'Violation85fTab',
    'Violation85FNS': 'Violation85fNsTab',
    'Violation85F5thTab': 'Violation85f5thTab',
    'ViolationMAX12Tab': 'ViolationMax12Tab',
    'ViolationMAX60Tab': 'ViolationMax60Tab'
}

def update_imports(content, file_mappings):
    """Update import statements in file content"""
    for old_name, new_name in file_mappings.items():
        old_module = old_name[:-3]  # Remove .py
        new_module = new_name[:-3]
        content = re.sub(
            f'from {old_module} import',
            f'from {new_module} import',
            content
        )
    return content

def update_class_references(content, class_mappings):
    """Update class references in file content"""
    for old_name, new_name in class_mappings.items():
        # Update class definitions
        content = re.sub(
            f'class {old_name}',
            f'class {new_name}',
            content
        )
        # Update isinstance checks
        content = re.sub(
            f'isinstance\\(([^,]+), {old_name}\\)',
            f'isinstance(\\1, {new_name})',
            content
        )
        # Update other references to the class name
        content = re.sub(
            f'\\b{old_name}\\b',
            new_name,
            content
        )
    return content

def main(dry_run=True):
    """Main execution function"""
    project_root = Path('.')
    
    print(f"{'DRY RUN: ' if dry_run else ''}Starting file and class rename process...")
    
    # First, check if all files exist
    for old_file in file_mappings.keys():
        if not (project_root / old_file).exists():
            print(f"Warning: {old_file} not found!")
            return
    
    # Get list of Python files to process (only in root directory)
    py_files = list(project_root.glob('*.py'))
    
    # Process each Python file
    for py_file in py_files:
        if py_file.name == 'rename_files.py':  # Skip this script
            continue
            
        print(f"\nProcessing: {py_file}")
        
        # Read content
        content = py_file.read_text(encoding='utf-8')
        original_content = content
        
        # Update imports and class references
        content = update_imports(content, file_mappings)
        content = update_class_references(content, class_mappings)
        
        # If content changed and not dry run, write it back
        if content != original_content:
            print(f"- Changes needed in {py_file}")
            if not dry_run:
                py_file.write_text(content, encoding='utf-8')
                print("  Changes written")
        else:
            print(f"- No changes needed in {py_file}")
    
    # Rename the files if not dry run
    if not dry_run:
        for old_name, new_name in file_mappings.items():
            old_path = project_root / old_name
            new_path = project_root / new_name
            if old_path.exists():
                old_path.rename(new_path)
                print(f"\nRenamed {old_name} to {new_name}")

if __name__ == "__main__":
    # First do a dry run
    print("=== Performing dry run ===")
    main(dry_run=True)
    
    # Ask for confirmation before making changes
    response = input("\nWould you like to proceed with the actual changes? (yes/no): ")
    if response.lower() == 'yes':
        print("\n=== Performing actual changes ===")
        main(dry_run=False)
    else:
        print("\nAborted. No changes were made.")