"""Sanitize the test database by anonymizing sensitive data."""
import random
import sqlite3
import string
from datetime import datetime

import pandas as pd


def generate_fake_name():
    """Generate a fake carrier name in 'lastname, f' format."""
    last_names = [
        "smith",
        "johnson",
        "williams",
        "brown",
        "jones",
        "garcia",
        "miller",
        "davis",
        "rodriguez",
        "martinez",
        "hernandez",
        "lopez",
        "gonzalez",
        "wilson",
        "anderson",
        "thomas",
        "taylor",
        "moore",
        "jackson",
        "martin",
        "lee",
        "perez",
        "thompson",
        "white",
        "harris",
        "sanchez",
        "clark",
        "ramirez",
        "lewis",
        "robinson",
        "walker",
        "young",
        "allen",
        "king",
        "wright",
        "scott",
        "torres",
        "nguyen",
        "hill",
        "flores",
        "green",
        "adams",
        "nelson",
        "baker",
        "hall",
        "rivera",
        "campbell",
        "mitchell",
        "carter",
        "roberts",
        "turner",
        "phillips",
        "evans",
        "parker",
        "edwards",
        "collins",
        "stewart",
        "morris",
        "murphy",
        "cook",
        "rogers",
        "morgan",
        "peterson",
        "cooper",
        "reed",
        "bailey",
        "bell",
        "gomez",
        "kelly",
        "howard",
        "ward",
        "cox",
        "diaz",
        "richardson",
        "wood",
        "watson",
        "brooks",
        "bennett",
        "gray",
        "james",
        "reyes",
        "cruz",
        "hughes",
        "price",
        "myers",
        "long",
        "foster",
        "sanders",
        "ross",
        "morales",
        "powell",
        "sullivan",
        "russell",
        "ortiz",
        "jenkins",
        "gutierrez",
        "perry",
        "butler",
        "barnes",
        "fisher",
        "henderson",
        "coleman",
    ]

    last_name = random.choice(last_names).lower()
    first_initial = random.choice(string.ascii_lowercase)
    return f"{last_name}, {first_initial}"


def generate_emp_id():
    """Generate a random 8-digit employee ID."""
    return "".join(random.choices(string.digits, k=8))


def sanitize_database(input_db, output_db):
    """Create a sanitized copy of the database."""
    try:
        # Connect to databases
        src_conn = sqlite3.connect(input_db)
        dst_conn = sqlite3.connect(output_db)

        # Tables we want to keep
        tables_to_keep = ["rings3", "carriers", "stations", "name_index"]

        print("Starting database sanitization...")

        # Get all carrier names from the carriers table
        carriers_df = pd.read_sql(
            "SELECT DISTINCT carrier_name FROM carriers", src_conn
        )
        real_names = carriers_df["carrier_name"].unique()

        # Create name mapping
        used_names = set()
        name_mapping = {}
        for name in real_names:
            while True:
                fake_name = generate_fake_name()
                if fake_name not in used_names:
                    used_names.add(fake_name)
                    name_mapping[name] = fake_name
                    break

        # Create station mapping
        stations_df = pd.read_sql("SELECT DISTINCT station FROM stations", src_conn)
        real_stations = stations_df["station"].unique()
        station_mapping = {}
        station_counter = 1

        for station in real_stations:
            if station.lower() == "out of station":
                station_mapping[station] = "OUT OF STATION"
            else:
                station_mapping[station] = f"STATION{station_counter}"
                station_counter += 1

        emp_id_mapping = {name: generate_emp_id() for name in real_names}

        # Process each table
        for table in tables_to_keep:
            print(f"\nProcessing table: {table}")

            # Read table schema
            cursor = src_conn.cursor()
            cursor.execute(
                f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'"
            )
            schema = cursor.fetchone()[0]

            # Create table in destination database
            dst_conn.execute(schema)

            # Read and process data
            df = pd.read_sql(f"SELECT * FROM {table}", src_conn)

            if table in ["rings3", "carriers"]:
                # Replace carrier names
                df["carrier_name"] = df["carrier_name"].map(name_mapping)

            if table in ["carriers", "stations"]:
                # Replace station names
                df["station"] = df["station"].map(station_mapping)

            elif table == "name_index":
                # Replace both TACS and KB names and employee IDs
                df["tacs_name"] = df["tacs_name"].map(name_mapping)
                df["kb_name"] = df["kb_name"].map(name_mapping)
                df["emp_id"] = df["tacs_name"].map(emp_id_mapping)

            # Write sanitized data
            df.to_sql(table, dst_conn, if_exists="replace", index=False)
            print(f"Processed {len(df)} rows")

        # Create a record of the sanitization
        with open("name_mapping.txt", "w") as f:
            f.write("Original Name -> Sanitized Name\n")
            f.write("===========================\n")
            for orig, fake in name_mapping.items():
                f.write(f"{orig} -> {fake}\n")
            f.write("\nStation Mapping:\n")
            f.write("===============\n")
            for orig, fake in station_mapping.items():
                f.write(f"{orig} -> {fake}\n")
            f.write(f"\nTotal unique names generated: {len(used_names)}")

        print("\nSanitization complete!")
        print(f"Sanitized database saved to: {output_db}")
        print("Mapping saved to: name_mapping.txt")

        # Close connections
        src_conn.close()
        dst_conn.close()

    except Exception as e:
        print(f"Error during sanitization: {str(e)}")
        raise


if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitize_database("test_db.sqlite", f"test_db_sanitized_{timestamp}.sqlite")
