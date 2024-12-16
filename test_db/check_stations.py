"""Check station information in the test database."""
import sqlite3

import pandas as pd


def check_station_info():
    """Inspect all station-related information in the database."""
    db_path = "test_db.sqlite"
    print(f"\nChecking database: {db_path}")

    conn = sqlite3.connect(db_path)

    print("\nChecking stations table:")
    print("=======================")
    stations_df = pd.read_sql("SELECT DISTINCT station FROM stations", conn)
    print(stations_df)

    print("\nChecking station info in carriers table:")
    print("=====================================")
    carrier_stations = pd.read_sql(
        "SELECT DISTINCT station FROM carriers ORDER BY station", conn
    )
    print(carrier_stations)

    print("\nSample carrier records with station:")
    print("=================================")
    sample_carriers = pd.read_sql(
        """
        SELECT carrier_name, station, list_status
        FROM carriers
        LIMIT 5
        """,
        conn,
    )
    print(sample_carriers)

    # Additional verification checks
    print("\nVerifying data sanitization:")
    print("===========================")

    # Check all station names
    all_stations = pd.read_sql(
        """
        SELECT station FROM carriers
        UNION
        SELECT station FROM stations
        """,
        conn,
    )
    non_standard = all_stations[
        ~all_stations["station"].isin(["OUT OF STATION", "STATION1"])
    ]
    if len(non_standard) > 0:
        print("WARNING: Found non-standard station names:")
        print(non_standard)
    else:
        print("✓ All station names are properly sanitized")

    # Check carrier name format
    carrier_names = pd.read_sql("SELECT DISTINCT carrier_name FROM carriers", conn)
    invalid_names = []
    for name in carrier_names["carrier_name"]:
        if "," not in name or len(name.split(",")) != 2:
            invalid_names.append(name)
        else:
            lastname, initial = name.split(",")
            if not lastname.strip().islower() or not initial.strip().islower():
                invalid_names.append(name)
            if len(initial.strip()) != 1:
                invalid_names.append(name)

    if invalid_names:
        print("\nWARNING: Found invalid carrier name formats:")
        for name in invalid_names:
            print(f"  - {name}")
    else:
        print("✓ All carrier names follow the correct format")

    conn.close()


if __name__ == "__main__":
    check_station_info()
