# Refactoring Plan: Moving Violation Tabs to Dedicated Directory

## Current Structure
- All violation tab files are in root directory
- Files to move:
  - base_violation_tab.py (base class)
  - violation_85d_tab.py
  - violation_85f_tab.py
  - violation_85f_5th_tab.py
  - violation_85f_ns_tab.py
  - violation_85g_tab.py
  - violation_max12_tab.py
  - violation_max60_tab.py
  - violations_summary_tab.py

## Phase 1: Initial Directory Setup and File Movement
1. Create new directory structure:
   ```
   eightbox/
   ├── tabs/
   │   ├── __init__.py
   │   ├── base/
   │   │   ├── __init__.py
   │   │   └── base_violation_tab.py
   │   └── violations/
   │       ├── __init__.py
   │       ├── violation_85d_tab.py
   │       ├── violation_85f_tab.py
   │       ├── violation_85f_5th_tab.py
   │       ├── violation_85f_ns_tab.py
   │       ├── violation_85g_tab.py
   │       ├── violation_max12_tab.py
   │       ├── violation_max60_tab.py
   │       └── violations_summary_tab.py
   ```

2. Update imports in all tab files to reflect new structure
3. Update main_gui.py imports to use new paths
4. Test functionality after move

## Phase 2: Code Organization in main_gui.py
1. Move tab initialization code to a new TabManager class
2. Update main_gui.py to use TabManager
3. Reduce code duplication in main_gui.py

## Questions/Concerns
1. Do we need to update any other files that might import these tab classes?
2. Should we update the build/deployment scripts to handle the new directory structure?
3. Do we need to update any test files?
4. Should we consider creating a TabFactory class in the future for better tab instantiation?

## Future Improvements
1. Consider creating a TabFactory class for better tab instantiation
2. Add better type hints and documentation in the new structure
3. Consider adding tab-specific configuration files
4. Consider moving tab-related utility functions to the tabs package

## Implementation Steps
1. Create new directory structure
2. Move files one at a time, testing after each move
3. Update imports in all files
4. Update main_gui.py to use new structure
5. Run all tests to ensure nothing is broken
6. Update documentation to reflect new structure

## Testing Strategy
1. Test each tab individually after moving
2. Test tab interactions
3. Test filtering and data display
4. Test all tab-specific functionality
5. Run existing test suite if available

## Rollback Plan
1. Keep backup of original files
2. Document all changes
3. Have git commits for each major step
4. Be prepared to revert if issues are found

## Success Criteria
1. All tabs function exactly as before
2. Code is more organized and maintainable
3. main_gui.py is significantly shorter
4. No regression in functionality
5. All tests pass 