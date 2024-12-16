# Test Database Documentation

This directory contains sanitized test data for the Eightbox application. All personally identifiable information has been anonymized while preserving the data patterns needed for testing.

## Files
- `test_db.sqlite`: Sanitized SQLite database containing carrier and clock ring data
- `sanitize_db.py`: Script for creating sanitized copies of production data
- `check_stations.py`: Verification script for checking data sanitization
- `verify_sanitized.py`: Additional verification utilities
- `name_mapping.txt`: Reference mapping between original and sanitized names (gitignored)

## Database Structure

### Tables
1. **rings3** - Clock Ring Data
   - rings_date: Date of work
   - carrier_name: Sanitized carrier name (format: "lastname, i")
   - total: Hours worked
   - moves: Movement codes/route info
   - code: Special codes
   - leave_type/leave_time: Leave information
   - bt/et: Begin time/End time

2. **carriers** - Carrier Information
   - effective_date: When status became effective
   - carrier_name: Sanitized carrier name
   - list_status: WAL/OTDL/NL status
   - ns_day: Non-scheduled day color code
   - route_s: Route number
   - station: Sanitized station name

3. **stations** - Station Information
   - station: Sanitized station names (STATION1, OUT OF STATION)

4. **name_index** - Name Mapping
   - tacs_name: Sanitized TACS name
   - kb_name: Sanitized KB name
   - emp_id: Randomized employee ID

## Data Characteristics
- All carrier names are anonymized in format: "lastname, i" (all lowercase)
- Station names are standardized to "STATION1" format (except OUT OF STATION)
- Employee IDs are randomized 8-digit numbers
- Work patterns, hours, and violation scenarios are preserved
- List status distributions match production patterns
- Date ranges and times are unchanged

## Verification
The `check_stations.py` script verifies:
1. All station names follow the standardized format
2. Carrier names follow the required format
3. Data integrity across related tables
4. No personally identifiable information remains

## Updating Test Data
To update the test data:
1. Place production database as `source_db.sqlite`
2. Run `sanitize_db.py` to create sanitized copy
3. Run verification scripts to ensure proper sanitization
4. Replace `test_db.sqlite` with new sanitized database

## Security Notes
- All personally identifiable information has been removed
- Station names are standardized to prevent location identification
- Random name generation ensures no correlation with real carriers
- Work patterns and violation scenarios are preserved for testing