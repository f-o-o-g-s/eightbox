# Date Selection Improvements Plan

## Current Functionality Analysis

### Database Integration
1. The date selection is critical for fetching clock ring data from the `rings3` table
2. Key database tables:
   - `rings3`: Contains clock ring data (rings_date, carrier_name, total, moves, etc.)
   - `carriers`: Contains carrier information (effective_date, list_status, route_s, etc.)

### Current Flow (To Be Changed)
1. User selects a Saturday in the calendar
2. On "Apply Date Range":
   - Fetches clock ring data for Saturday through Friday (7 days)
   - Validates database and carrier list
   - Processes violations and updates all violation tabs
   - Updates OTDL maximization data

### Current Limitations
1. Users must guess which dates have available data
2. No visual indication of valid date ranges
3. Possible to select invalid dates (non-Saturdays)
4. No way to know data availability without trying

## New Approach: Available Date Ranges

### Core Concept
Instead of a calendar widget, show users a structured view of available date ranges:
1. Data Organization:
   - Show all available weekly ranges (Saturday-Friday)
   - Dynamically growing dataset (new data added weekly/bi-weekly)
   - Focus on simple, efficient display
2. Only show date ranges that have data in the database
3. Eliminate possibility of selecting invalid dates

### UI Structure: Tree-Table Hybrid
1. Structure:
   ```
   Currently Selected: Mar 9 - Mar 15, 2024 (or "No Date Range Selected")

   Year  Month     Date Range         Carriers
   ▼ 2024
     ▼ March
       │           Mar 2 - Mar 8         45    
       │           Mar 9 - Mar 15        43    [Selected]
       │           Mar 16 - Mar 22       44    
     ▼ February
       │           Feb 3 - Feb 9         42    
       │           Feb 10 - Feb 16       45    
   ```
2. Benefits:
   - Combines hierarchical organization with tabular data
   - Matches existing application's table-based UI style
   - Clear indication of current selection
   - Room for future enhancements

### Technical Implementation

#### Data Gathering
1. Query Database for Available Dates:
   ```sql
   SELECT 
       rings_date,
       COUNT(DISTINCT carrier_name) as carrier_count
   FROM rings3 
   GROUP BY rings_date
   ORDER BY rings_date DESC
   ```
2. Process Results:
   - Group into Saturday-Friday ranges
   - Calculate weekly carrier counts
   - Store in appropriate data structure

#### UI Components
1. Main View:
   - Tree-table hybrid widget
   - Current selection display
   - Column headers for basic information
2. Supporting Elements:
   - Auto-refresh on startup
   - Manual refresh button
   - Loading indicator

### Core Features
1. Data Display:
   - Date range in clear format
   - Carrier count per week
   - Clear indication of selected range
2. Basic Actions:
   - Select date range
   - Apply selection
   - Refresh data

## Implementation Phases

### Phase 1: Core Structure
1. Create new DateRangeSelector component
2. Implement database query for available dates
3. Build basic tree-table structure
4. Add selection logic

### Phase 2: Integration
1. Add carrier count column
2. Implement auto-refresh on startup
3. Add manual refresh button
4. Create loading states

### Phase 3: Polish
1. Refine Material Design styling
2. Add selection highlighting
3. Improve error handling
4. Add loading animations

## Technical Considerations
1. Performance:
   - Efficient date range queries
   - Handle growing dataset gracefully
2. UI/UX:
   - Material Design consistency
   - Clear visual hierarchy
   - Obvious current selection
3. Data Management:
   - Auto-refresh on startup
   - Manual refresh option
   - Clear loading states

## Next Steps
1. Implement basic tree-table structure
2. Test with sample data
3. Integrate with existing date range handling
4. Add current selection display