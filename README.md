# Eightbox

A Windows desktop application built with PyQt5 for a local union branch to track and analyze carrier violations using data from klusterbox's mandates.sqlite file.

## Features

### Violation Detection
- 8.5.D Violations (Overtime Off Route when OTDL wasn't utilized to their hourly limits)
- 8.5.F Violations (Over 10, Non-Scheduled, 5th Day)
- 8.5.G Violations (OTDL Maximization)
- MAX12 Violations (12-Hour Daily Limit)
- MAX60 Violations (60-Hour Weekly Limit)
- Comprehensive violation summaries with remedy calculations

### OTDL Maximization Checking
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

## Requirements

### Runtime Dependencies
- Python 3.11 or higher
- PyQt5 == 5.15.11 (with Qt5 5.15.2)
- pandas == 2.2.3
- openpyxl == 3.1.5
- numpy == 2.2.0
- xlsxwriter == 3.2.0
- PyGithub == 2.5.0 (for release management)
- sqlite3 (included with Python)

### Development Dependencies
- black == 24.10.0 (code formatting)
- flake8 == 7.1.1 (style guide)
- isort == 5.13.2 (import sorting)
- pre-commit == 4.0.1 (git hooks)
- pylint == 3.3.2 (additional linting)

## Setup

### Prerequisites
1. Install and configure [Klusterbox](https://github.com/TomOfHelatrobus/klusterbox)
   - Alternatively, you can use the test database included in this repository
3. Ensure Klusterbox is working correctly with your data
4. ⚠️ **IMPORTANT**: Always backup your Klusterbox database before use:
   ```
   cd %USERPROFILE%\Documents\.klusterbox
   copy mandates.sqlite mandates.sqlite.backup
   ```
   While Eightbox should not modify your Klusterbox database, it's always wise to have a backup.

### Installation
1. Download the latest release (.7z file) from the GitHub releases page
2. Extract the .7z file to a new folder named `eightbox`
3. Launch `eightbox.exe` from the extracted folder

### Configuration
- Eightbox will automatically:
  - Detect your Klusterbox database location
  - Create its own `eightbox.sqlite` file (a mirror of mandates.sqlite)
  - Sync with mandates.sqlite on startup

### Database Synchronization
Eightbox automatically syncs with Klusterbox's database. If you update data in Klusterbox while Eightbox is running:
1. Go to Settings > Database Path
2. Click "Sync Database" to manually update Eightbox's data

## Test Database
The repository includes a sanitized test database (`fake_mandates_db.sqlite`) that you can use to try out the application without needing real carrier data. This database:
- Contains anonymized carrier names and employee IDs
- Includes sample data for all supported violation types
- Uses generic station names (STATION1, STATION2, etc.)
- Is safe to use and share as it contains no real carrier information

To use the test database:
1. First, backup your existing Klusterbox database:
   ```
   cd %USERPROFILE%\Documents\.klusterbox
   copy mandates.sqlite mandates.sqlite.backup
   ```
2. Copy the test database to the Klusterbox directory:
   ```
   copy path\to\fake_mandates_db.sqlite %USERPROFILE%\Documents\.klusterbox\mandates.sqlite
   ```
3. Launch Eightbox - it will automatically detect the database

You can also use the test database as a template to understand the required schema for your own data.

To restore your original database:
```
cd %USERPROFILE%\Documents\.klusterbox
copy mandates.sqlite.backup mandates.sqlite
```

## Usage

⚠️ **IMPORTANT**: Always verify clock ring information with the Employee Everything Report obtained through a Request for Information (RFI). This report is the source of truth for clock ring data. Never rely solely on the program's violation detection - while the program aims to be accurate, there may be bugs or data inconsistencies that could affect results. Also the remedies are based on the branch settlements and escalated remedies, so they may not be universally applicable.

### Basic Workflow
1. Click on Date Selection
2. Find a date range you want to investigate
3. Setup your carrier list when prompted
4. Configure carrier settings:
   - Set carrier status and hourly limits (primarily for OTDL)
   - Remove carriers from investigation if needed (can be restored via "Removed" button)
   - Click Save (settings stored in `carrier_list.json`)

### Violation Detection
5. The program will analyze the date range for violations
6. OTDL Maximization management:
   - Excuse OTDL carriers who didn't reach their hour limits
   - Apply changes to update violations and remedies

### Data Cleanup (Optional)
7. For detailed analysis, use File > Clean Invalid Moves to fix problematic clock rings:
   - Look for moves > 4.25 hours (possible scanner/editing issues)
   - Check for invalid route numbers (e.g., rt0000)
   - Use Employee Everything Report as reference
   - Click "Save All" to apply fixes

### Export and Documentation
8. Generate reports:
   - File > Generate All Excel Spreadsheets
   - Creates 8 Excel files in `eightbox/spreadsheets/daterange/`
   - Each file includes daily sub-tabs as worksheets
   - Preserves formatting and colors from Eightbox

### Notes
- Manual cell editing is possible but won't affect violation detection
- Help > Article 8 Violation Formulas Documentation explains detection methods
- Violation detection is based on specific branch settlements and escalated remedies
- MAX60/MAX12 violations may be more universally applicable
- Always verify violations manually as the program's detection is not infallible
- Cross-reference all findings with the Employee Everything Report before taking action
- Remember that this tool is meant to assist in violation detection, not replace human verification

## Development
This project uses:
- black for code formatting
- flake8 for style guide enforcement
- isort for import sorting

### Pre-commit Hooks
The project uses pre-commit hooks to ensure code quality:
- isort: Sorts Python imports
- black: Formats Python code
- flake8: Checks code style
- Conventional Commit: Enforces commit message format

To set up pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

## Version History

### 2024.1.3.2
- Added cancel button functionality to progress dialogs
- Enhanced progress dialog styling with Material Design theme
- Improved user control over long-running operations

### 2024.1.3.1
- Improved removed carriers manager UI with single selection and simplified view
- Added proper UTF-8 encoding to all file operations
- Fixed restore button functionality in removed carriers manager
- Removed unused code and improved code quality

### 2024.1.3.0
- Added 7-Zip compression for smaller distribution files
- Improved GitHub release upload handling
- Added fallback to ZIP if 7-Zip is not available

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