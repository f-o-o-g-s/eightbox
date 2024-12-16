# Eightbox

A Windows desktop application built with PyQt5 for a local union branch to track and analyze carrier violations using data from klusterbox's mandates.sqlite file.

## Features

### Violation Tracking
- 8.5.D Violations (Overtime Off Route)
- 8.5.F Violations (Regular, Non-Scheduled, 5th Day)
- 8.5.G Violations (OTDL Maximization)
- MAX12 Violations (12-Hour Daily Limit)
- MAX60 Violations (60-Hour Weekly Limit)
- Comprehensive violation summaries with remedy calculations

### OTDL Management
- OTDL Maximization tracking and status management
- Carrier excusal system for 8.5.G violations
- Single-click application of changes across multiple dates
- Real-time violation updates when maximization status changes

### Data Management
- Import carrier data from JSON
- Customizable carrier list management
- Date-based violation filtering
- Excel export functionality with consistent carrier name sorting
- Progress tracking for long operations

### User Interface
- Modern PyQt5 interface with Material Dark theme
- Tabbed interface for different violation types
- Global carrier filtering across all tabs
- Comprehensive documentation for all violation types
- Real-time progress feedback for long operations

## Requirements

### Runtime Dependencies
- Python 3.11 or higher
- PyQt5 >= 5.15.2
- pandas >= 2.2.3
- openpyxl >= 3.1.5
- numpy >= 1.24.0
- xlsxwriter >= 3.1.2
- PyGithub >= 2.1.1 (for release management)
- sqlite3 (included with Python)

### Development Dependencies
- black (code formatting)
- flake8 (style guide)
- isort (import sorting)

## Setup
[Installation instructions to be added]

## Test Database
The repository includes a sanitized test database (`fake_mandates_db.sqlite`) that you can use to try out the application without needing real carrier data. This database:
- Contains anonymized carrier names and employee IDs
- Includes sample data for all supported violation types
- Uses generic station names (STATION1, STATION2, etc.)
- Is safe to use and share as it contains no real carrier information

To use the test database:
1. Launch the application
2. Click Settings > Database Path in the menu bar
3. Set the database path to `fake_mandates_db.sqlite` in your project directory
4. Click Save to apply the changes

You can also use the test database as a template to understand the required schema for your own data.

## Usage
[Basic usage instructions to be added]

## Development
This project uses:
- black for code formatting
- flake8 for style guide enforcement
- isort for import sorting

## Version History

### 2024.0.4.0
- Added 8.5.G violation detection and OTDL Maximization integration
- Added comprehensive documentation for all violation types
- Improved UI with single Apply button for OTDL Maximization
- Enhanced Excel export with consistent carrier name sorting
- Added progress dialogs for better user feedback
- Fixed various bugs and improved overall stability

## License
MIT License