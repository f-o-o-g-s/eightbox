# Violation Detection Refactoring Plan

## Goal
Split violation formulas from violation_detection.py into separate files for better maintainability and testing.

## Original Files
- violation_detection.py (main logic)
- violation_detection_original.py (backup reference)

## Formula Files to Create
1. violation_formulas/
   - ✓ article_85d.py (Off-assignment violations)
   - article_85f.py (Regular overtime violations)
   - article_85f_ns.py (Non-scheduled day violations)
   - article_85f_5th.py (5th day overtime violations)
   - article_85g.py (OTDL maximization violations)
   - max_violations.py (12/60 hour violations)
   - ✓ __init__.py (for package imports)

## Progress Tracking

### Moved Functions
- [x] detect_85d_violations -> article_85d.py
- [x] calculate_85d_remedies -> article_85d.py

### To Move
1. Article 8.5.D Functions:
   - [x] detect_85d_violations
   - [x] calculate_85d_remedies

2. Article 8.5.F Functions:
   - [ ] detect_85f_violations
   - [ ] calculate_85f_remedies
   - [ ] detect_85f_ns_violations
   - [ ] calculate_85f_ns_remedies
   - [ ] detect_85f_5th_violations
   - [ ] calculate_85f_5th_remedies

3. Article 8.5.G Functions:
   - [ ] detect_85g_violations
   - [ ] calculate_85g_remedies

4. MAX Violation Functions:
   - [ ] detect_max12_violations
   - [ ] detect_max60_violations
   - [ ] calculate_max_remedies

## Testing Steps
1. Move one formula file at a time
2. Update imports in violation_detection.py
3. Test each violation type after moving
4. Verify results match original implementation

## Manual Testing Plan for 8.5.D
1. Run main_gui.py
2. Load some test data
3. Check if 8.5.D violations are still detected correctly
4. Verify remedy calculations match original implementation
5. Check if the violations display properly in the UI

## Notes
- Keep shared utility functions in violation_detection.py
- Maintain backwards compatibility with existing tab implementations
- Document any improvements or bug fixes found during refactoring
