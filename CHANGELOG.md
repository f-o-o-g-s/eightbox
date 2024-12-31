# Changelog

## [2024.1.6.3] - 2024-12-31
- Updated parent/child tab colors for better visual hierarchy
- Improved main GUI and filter button styles
- Fixed OTDL window size to prevent row cutoff



## [2024.1.6.2] - 2024-12-29
- Updated theme to official Rosé Pine colors
- Improved code formatting and linting
- Enhanced filter button styling



## [2024.1.6.1] - 2024-12-29
- Fixed bug in Article 8.5.F and 8.5.F NS violation detection where No Violation and remedy_total=0.0 were not explicitly initialized
- Improved consistency in violation type and remedy total handling



## [2024.1.6.0] - 2024-12-29
- Modernized table view styling in base violation tab
- Improved button styling consistency across OTDL and date selection
- Enhanced carrier list pane button styling
- Modified removed carriers manager table header for better visibility



## [2024.1.5.1] - 2024-12-29
- Made violation tables read-only to prevent accidental data modification
- Updated documentation to reflect read-only tables



## [2024.1.5.0] - 2024-12-29
- Implemented new Rose Pine / Material Design hybrid theme system
- Unified all application styling in theme.py
- Improved UI consistency and readability across all dialogs
- Reorganized code structure for better maintainability
- Fixed various styling and UI-related bugs



## [2024.1.4.2] - 2024-12-27
- Fixed version formatting in README.md version history
- Improved logic to maintain exactly 3 most recent versions
- Preserved original version number format



## [2024.1.4.1] - 2024-12-27
- Fixed release script to include changelog and readme updates in release commit



## [2024.1.4.0] - 2024-12-27
- Added new worker system for violation processing
- Improved error handling and cleanup
- Fixed progress dialog duplication issue
- Preserved tab selection in violations summary tab after OTDL maximization updates



## [2024.1.3.3] - 2024-12-26
- Created CHANGELOG.md for full version history
- Updated README.md to show recent changes only
- Modified release.py to maintain both files



All notable changes to Eightbox will be documented in this file.

## [2024.1.3.2] - 2024-12-26
- Added cancel button functionality to progress dialogs
- Enhanced progress dialog styling with Material Design theme
- Improved user control over long-running operations

## [2024.1.3.1] - 2024-12-25
- Improved removed carriers manager UI with single selection and simplified view
- Added proper UTF-8 encoding to all file operations
- Fixed restore button functionality in removed carriers manager
- Removed unused code and improved code quality

## [2024.1.3.0] - 2024-12-25
- Added 7-Zip compression for smaller distribution files
- Improved GitHub release upload handling
- Added fallback to ZIP if 7-Zip is not available

## [2024.1.2.1] - 2024-12-24
- Fixed OTDL carrier excusal handling in 8.5.G violations
- Improved case-insensitive carrier name matching
- Enhanced excusal data handling in violation detection

## [2024.1.2.0] - 2024-12-24
- Added removed carriers management functionality
- Implemented restore functionality for removed carriers
- Enhanced carrier list UI with better button layout
- Improved carrier removal workflow
- Updated database initialization for removed carriers tracking

## [2024.1.0.6] - 2024-12-23
- Fixed linting issues and line length problems
- Removed redundant code and comments
- Updated clean moves functionality to use eightbox.sqlite
- Improved code organization

## [2024.1.0.5] - 2024-12-23
- Updated clean moves functionality to use eightbox.sqlite
- Fixed database synchronization issues in clean moves dialog
- Improved database path handling consistency across application

## [2024.1.0.4] - 2024-12-22
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

## [2024.0.11.0] - 2024-12-21
- Updated all violation type documentation to reflect current implementation
- Enhanced documentation with highlighted key contract language sections
- Added detailed explanations for vectorized violation detection
- Improved documentation formatting and styling consistency
- Added clarification about exact excusal indicator matching
- Enhanced examples with consistent decimal formatting
- Added missing violation types and clarified hour limit defaults

## [2024.0.10.0] - 2024-12-20
- Vectorized violation detection for significant performance improvements
- Fixed 85G violation detection to match original behavior
- Standardized display_indicator naming across codebase
- Updated OTDL maximization pane for consistency

## [2024.0.9.0] - 2024-12-19
- Enhanced carrier list UI with Material Design improvements
- Added Material Design styling to carrier list interface
- Improved visual feedback and status indicators
- Added Unicode search icon to carrier filter
- Enhanced table styling with better spacing and borders
- Removed old carrier list implementation

## [2024.0.8.1] - 2024-12-18
- Enhanced release.py with non-interactive mode
- Added support for automated releases

## [2024.0.8.0] - 2024-12-18
- Implemented December exclusion period for violation detection
- Updated violation detection logic for December exclusionary period
- Added configurable JSON file for pay period dates
- Updated 8.5.F, 8.5.G, MAX12, and MAX60 violation detection
- Improved trigger carrier display in 8.5.G daily tabs

## [2024.0.7.0] - 2024-12-17
- Improved database sync functionality with better error handling
- Changed calendar date range selection to table view
- Enhanced settings dialog with improved sync completion messages
- Updated UI styling for OTDL maximization and Edit Carrier dialogs
- Fixed date range selection bugs
- Removed merge moves functionality in favor of Edit Moves
- Added automatic status display refresh after sync operations

## [2024.0.6.0] - 2024-12-16
- Added carrier list migration dialog for database changes
- Improved settings dialog with database path handling
- Added sanitized test database for development and testing
- Enhanced project documentation and README
- Fixed UI styling and dialog sizing issues
- Improved code formatting and organization

## [2024.0.5.0] - 2024-12-15
- Fixed OTDL excusal order precedence
- Improved code quality with extensive pylint fixes
- Enhanced method naming conventions across codebase
- Fixed code style issues in multiple modules
- Improved error handling and parameter validation

## [2024.0.4.4, 2024.0.4.3] - 2024-12-14
- Fixed OTDL excusal order precedence in violation detection
- Improved auto-excusal status handling

## [2024.0.4.2] - 2024-12-14
- Modified 8.5.D violation detection to handle NS days
- Updated move requirements for regular vs NS days

## [2024.0.4.1] - 2024-12-13
- Improved hour display in violation tabs
- Fixed highlighting logic in MAX60 tab
- Updated MAX12 Summary tab to show total hours
- Enhanced violation table sorting

## [2024.0.4.0] - 2024-12-13
- Added 8.5.G violation detection and OTDL Maximization integration
- Added comprehensive documentation for all violation types
- Improved UI with single Apply button for OTDL Maximization
- Enhanced Excel export with consistent carrier name sorting
- Added progress dialogs for better user feedback
- Fixed various bugs and improved overall stability 