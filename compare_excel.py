import pandas as pd
import numpy as np
from pathlib import Path

def compare_excel_files(file1_path, file2_path):
    """Compare two Excel files and show differences."""
    print(f"\nComparing {Path(file1_path).name} with {Path(file2_path).name}...")
    
    # Read Excel files
    df1 = pd.read_excel(file1_path)
    df2 = pd.read_excel(file2_path)
    
    # Sort both DataFrames by carrier_name and date to ensure proper comparison
    df1 = df1.sort_values(['carrier_name', 'date']).reset_index(drop=True)
    df2 = df2.sort_values(['carrier_name', 'date']).reset_index(drop=True)
    
    # Print basic statistics
    print("\nBasic Statistics:")
    print(f"File 1 rows: {len(df1)}")
    print(f"File 2 rows: {len(df2)}")
    
    # Check for column differences
    cols1 = set(df1.columns)
    cols2 = set(df2.columns)
    
    if cols1 != cols2:
        print("\nColumn differences:")
        print(f"Columns only in file 1: {cols1 - cols2}")
        print(f"Columns only in file 2: {cols2 - cols1}")
        common_cols = list(cols1.intersection(cols2))
    else:
        common_cols = list(cols1)
    
    # Compare data in common columns
    print("\nChecking for data differences...")
    
    # Initialize counters
    total_differences = 0
    differences_by_type = {}
    
    # Compare row by row
    for idx in range(min(len(df1), len(df2))):
        row1 = df1.iloc[idx]
        row2 = df2.iloc[idx]
        
        for col in common_cols:
            val1 = row1[col]
            val2 = row2[col]
            
            # Handle NaN comparisons
            if pd.isna(val1) and pd.isna(val2):
                continue
                
            # Handle numeric comparisons with tolerance
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                if not np.isclose(val1, val2, rtol=1e-05, atol=1e-08):
                    diff_key = f"{row1['carrier_name']} - {row1['date']} - {col}"
                    differences_by_type[diff_key] = f"{val1} vs {val2}"
                    total_differences += 1
            # Handle string comparisons
            elif str(val1) != str(val2):
                diff_key = f"{row1['carrier_name']} - {row1['date']} - {col}"
                differences_by_type[diff_key] = f"{val1} vs {val2}"
                total_differences += 1
    
    # Print differences
    if total_differences == 0:
        print("\nNo differences found in the data!")
    else:
        print(f"\nFound {total_differences} differences:")
        for key, value in differences_by_type.items():
            print(f"{key}: {value}")
    
    # Compare violation type counts
    print("\nViolation Type Counts Comparison:")
    counts1 = df1['violation_type'].value_counts()
    counts2 = df2['violation_type'].value_counts()
    
    all_types = sorted(set(counts1.index) | set(counts2.index))
    print("\nViolation Type Counts:")
    print(f"{'Violation Type':<40} {'File 1':>10} {'File 2':>10} {'Diff':>10}")
    print("-" * 72)
    
    for vtype in all_types:
        count1 = counts1.get(vtype, 0)
        count2 = counts2.get(vtype, 0)
        diff = count1 - count2
        print(f"{vtype:<40} {count1:>10} {count2:>10} {diff:>10}")

if __name__ == "__main__":
    # Get file paths from user
    file1 = input("Enter path to first Excel file (vectorized): ")
    file2 = input("Enter path to second Excel file (main): ")
    
    try:
        compare_excel_files(file1, file2)
    except Exception as e:
        print(f"\nError comparing files: {e}") 