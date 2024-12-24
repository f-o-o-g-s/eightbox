# Eightbox Backup System Instructions

This document provides detailed instructions for AI assistants about the Eightbox project's backup system.

## Overview

The backup system consists of two main components:
1. Git-based version control with structured commit messages
2. ZIP-based file backups with intelligent file filtering

## Commit Message Format

All commit messages must follow this structure:
```
BACKUP (YYYY-MM-DD HH:MM): <prefix>: <description>
```

### Valid Prefixes
- `Fix:` - For bug fixes, minor improvements, and routine changes (default)
- `Feature:` - For new features, major enhancements, or new functionality
- `Breaking:` - For changes that break backward compatibility

### Examples
```bash
python backup.py "Update documentation"  # Will become: BACKUP (2024-12-24 14:54): Fix: Update documentation
python backup.py "Feature: Add new violation detection"
python backup.py "Breaking: Change database schema"
```

## Pre-commit Hooks

Before each commit, the following checks are automatically run:

1. `isort`
   - Sorts Python imports
   - Maintains consistent import order
   - Auto-fixes issues when possible

2. `black`
   - Formats Python code
   - Uses 88 character line length
   - Auto-fixes formatting issues

3. `flake8`
   - Checks code style
   - Reports PEP 8 violations
   - Identifies potential errors

The system will automatically retry up to 3 times if formatting tools modify files.

## ZIP Backup System

The ZIP backup functionality:
- Creates timestamped ZIP archives
- Filters out unnecessary files (cache, compiled files, etc.)
- Always includes critical files and directories
- Maintains the project's directory structure

### Special Handling
- `/database` directory is always included
- `/tabs` directory is always included
- Configuration files are always included
- Virtual environment and cache directories are excluded

## Error Handling

The backup system includes robust error handling:
1. Pre-commit hook failures are reported with clear messages
2. Git operation failures include detailed error information
3. ZIP backup errors are caught and reported
4. Unicode encoding issues are handled gracefully

## Usage for AI Assistants

When suggesting changes or commits:
1. Always use the appropriate prefix based on the change type
2. Default to `Fix:` for routine changes
3. Use `Feature:` for new functionality
4. Use `Breaking:` for backward-incompatible changes

### Do Not
- Do not suggest custom prefixes
- Do not modify the timestamp format
- Do not bypass the pre-commit hooks
- Do not suggest direct git commands (use backup.py instead)

### Do
- Suggest descriptive commit messages
- Recommend appropriate prefixes
- Help users understand error messages
- Guide users through the backup process 