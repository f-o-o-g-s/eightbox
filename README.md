# Eightbox

A Windows desktop application built with PyQt5 for a local union branch to track and analyze carrier violations using data from klusterbox's mandates.sqlite file.

## Features

### Violation Tracking
- 8.5.D Violations (Overtime Off Route when OTDL wasn't utilized to their hourly limits)
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
- Removed carriers management with restore functionality
- Date-based violation filtering
- Excel export functionality with consistent carrier name sorting
- Progress tracking for long operations

### User Interface
- Modern PyQt5 interface with Material Dark theme
- Tabbed interface for different violation types
- Global carrier filtering across all tabs
- Comprehensive documentation for all violation types
- Real-time progress feedback for long operations

## Documentation

Documentation is maintained in the `feature/add-documentation` branch using MkDocs with Material theme.

### Documentation Workflow

1. Switch to documentation branch:
   ```bash
   git checkout feature/add-documentation
   ```

2. Install MkDocs if needed:
   ```bash
   python -m pip install mkdocs-material
   ```

3. Preview documentation:
   ```bash
   cd docs && python -m mkdocs serve
   ```
   Then visit http://127.0.0.1:8000

4. Edit documentation files in `docs/src/`
   - Main pages are in the root
   - Feature docs in `features/`
   - User guide in `user-guide/`

5. When done:
   - Stop the server (Ctrl+C)
   - Commit your changes
   - The `site/` directory can be safely deleted (it's regenerated as needed)

6. Switch back to main:
   ```bash
   git checkout main
   ```

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

### 2024.1.2.1
- Fixed OTDL carrier excusal handling in 8.5.G violations
- Improved case-insensitive carrier name matching
- Enhanced excusal data handling in violation detection

### 2024.1.2.0
- Added removed carriers management functionality
- Implemented restore functionality for removed carriers
- Enhanced carrier list UI with better button layout
- Improved carrier removal workflow
- Updated database initialization for removed carriers tracking

### 2024.1.0.6
- Fixed linting issues and line length problems
- Removed redundant code and comments
- Updated clean moves functionality to use eightbox.sqlite
- Improved code organization

### 2024.1.0.5
- Updated clean moves functionality to use eightbox.sqlite
- Fixed database synchronization issues in clean moves dialog
- Improved database path handling consistency across application

### 2024.1.0.4
- Fixed 85F 5th violation detection and highlighting
- Fixed formula to exclude NS days when determining 5th overtime day
- Corrected remedy calculations for 85F 5th violations
- Updated summary tab to properly identify NS days using display_indicator
- Fixed violation date highlighting in UI
- Major code refactoring:
  - Split database functionality into dedicated modules (models, path_manager, service)
  - Moved violation tab files to dedicated tabs directory
  - Improved code organization and error handling
  - Enhanced UI component initialization

### 2024.0.11.0
- Updated all violation type documentation to reflect current implementation
- Enhanced documentation with highlighted key contract language sections
- Added detailed explanations for vectorized violation detection
- Improved documentation formatting and styling consistency
- Added clarification about exact excusal indicator matching
- Enhanced examples with consistent decimal formatting
- Added missing violation types and clarified hour limit defaults

### 2024.0.10.0
- Vectorized violation detection for significant performance improvements
- Fixed 85G violation detection to match original behavior
- Standardized display_indicator naming across codebase
- Updated OTDL maximization pane for consistency

### 2024.0.9.0
- Enhanced carrier list UI with Material Design improvements
- Added Material Design styling to carrier list interface
- Improved visual feedback and status indicators
- Added Unicode search icon to carrier filter
- Enhanced table styling with better spacing and borders
- Removed old carrier list implementation

### 2024.0.8.1
- Enhanced release.py with non-interactive mode
- Added support for automated releases

### 2024.0.8.0
- Implemented December exclusion period for violation detection
- Updated violation detection logic for December exclusionary period
- Added configurable JSON file for pay period dates
- Updated 8.5.F, 8.5.G, MAX12, and MAX60 violation detection
- Improved trigger carrier display in 8.5.G daily tabs

### 2024.0.7.0
- Improved database sync functionality with better error handling
- Changed calendar date range selection to table view
- Enhanced settings dialog with improved sync completion messages
- Updated UI styling for OTDL maximization and Edit Carrier dialogs
- Fixed date range selection bugs
- Removed merge moves functionality in favor of Edit Moves
- Added automatic status display refresh after sync operations

### 2024.0.6.0
- Added carrier list migration dialog for database changes
- Improved settings dialog with database path handling
- Added sanitized test database for development and testing
- Enhanced project documentation and README
- Fixed UI styling and dialog sizing issues
- Improved code formatting and organization

### 2024.0.5.0
- Fixed OTDL excusal order precedence
- Improved code quality with extensive pylint fixes
- Enhanced method naming conventions across codebase
- Fixed code style issues in multiple modules
- Improved error handling and parameter validation

### 2024.0.4.4, 2024.0.4.3
- Fixed OTDL excusal order precedence in violation detection
- Improved auto-excusal status handling

### 2024.0.4.2
- Modified 8.5.D violation detection to handle NS days
- Updated move requirements for regular vs NS days

### 2024.0.4.1
- Improved hour display in violation tabs
- Fixed highlighting logic in MAX60 tab
- Updated MAX12 Summary tab to show total hours
- Enhanced violation table sorting

### 2024.0.4.0
- Added 8.5.G violation detection and OTDL Maximization integration
- Added comprehensive documentation for all violation types
- Improved UI with single Apply button for OTDL Maximization
- Enhanced Excel export with consistent carrier name sorting
- Added progress dialogs for better user feedback
- Fixed various bugs and improved overall stability

## License

MIT License