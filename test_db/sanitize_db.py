"""Sanitize the test database by anonymizing sensitive data."""
import random
import sqlite3
import string
import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

# Expanded list of last names (over 1000 common surnames)
LAST_NAMES = [
    # Original 100 common names
    "smith", "johnson", "williams", "brown", "jones", "garcia", "miller", "davis",
    "rodriguez", "martinez", "hernandez", "lopez", "gonzalez", "wilson", "anderson",
    "thomas", "taylor", "moore", "jackson", "martin", "lee", "perez", "thompson",
    "white", "harris", "sanchez", "clark", "ramirez", "lewis", "robinson", "walker",
    "young", "allen", "king", "wright", "scott", "torres", "nguyen", "hill", "flores",
    "green", "adams", "nelson", "baker", "hall", "rivera", "campbell", "mitchell",
    "carter", "roberts", "turner", "phillips", "evans", "parker", "edwards", "collins",
    "stewart", "morris", "murphy", "cook", "rogers", "morgan", "peterson", "cooper",
    "reed", "bailey", "bell", "gomez", "kelly", "howard", "ward", "cox", "diaz",
    "richardson", "wood", "watson", "brooks", "bennett", "gray", "james", "reyes",
    "cruz", "hughes", "price", "myers", "long", "foster", "sanders", "ross", "morales",
    "powell", "sullivan", "russell", "ortiz", "jenkins", "gutierrez", "perry", "butler",
    "barnes", "fisher", "henderson", "coleman",
    # Additional names for more variety
    "alexander", "armstrong", "ashworth", "atkinson", "austin", "baldwin", "ball",
    "barker", "barlow", "barrett", "barton", "bates", "baxter", "beattie", "benson",
    "bishop", "black", "blackburn", "bolton", "bond", "booth", "bradley", "brady",
    "brennan", "briggs", "broadhurst", "brock", "burgess", "burns", "burton", "byrne",
    "cameron", "carr", "carroll", "carson", "chapman", "chase", "chen", "clarke",
    "clayton", "cole", "conway", "cooke", "cooper", "corbett", "costello", "cowell",
    "crawford", "cross", "cunningham", "curtis", "dale", "dalton", "daly", "daniels",
    "darby", "davidson", "davies", "dawson", "day", "dean", "decker", "delaney",
    "dennis", "dixon", "doyle", "drake", "dudley", "duffy", "duncan", "dunne",
    "elliott", "ellis", "emerson", "england", "english", "evans", "fairfax", "farrell",
    "faulkner", "ferguson", "field", "finch", "fitzgerald", "fleming", "fletcher",
    "flynn", "ford", "forrest", "forsyth", "fox", "francis", "franklin", "fraser",
    "freeman", "french", "frost", "gallagher", "gardner", "garner", "george", "gibson",
    "gilbert", "gill", "glover", "goodman", "gordon", "graham", "grant", "graves",
    "gregory", "griffin", "griffiths", "grove", "gunner", "hale", "haley", "hamilton",
    "hammond", "hancock", "hardy", "harmon", "harper", "harrison", "hart", "harvey",
    "hawkins", "hayes", "haynes", "heath", "henderson", "henry", "herbert", "hewitt",
    "hicks", "higgins", "hodges", "hoffman", "hogan", "holden", "holland", "holmes",
    "holt", "hopkins", "horton", "hudson", "hunt", "hunter", "hutchinson", "hyde",
    "ingram", "irwin", "jackson", "jacobson", "james", "jefferson", "jenkins",
    "jennings", "jensen", "johnson", "johnston", "jones", "jordan", "joyce", "kane",
    "kaur", "keating", "kelly", "kendall", "kennedy", "kent", "khan", "king",
    "kingston", "knight", "knowles", "knox", "lambert", "lane", "lawrence", "lawson",
    "leach", "lee", "leonard", "leslie", "levine", "levy", "lewis", "lindsay",
    "little", "livingston", "lloyd", "logan", "london", "long", "love", "lowe",
    "lucas", "lynch", "lyons", "macdonald", "mackenzie", "madison", "malone", "mann",
    "manning", "marsh", "marshall", "mason", "matthews", "maxwell", "mccarthy",
    "mccormick", "mcdonald", "mcgrath", "mcguire", "mckay", "mckenzie", "mclean",
    "mcleod", "meadows", "medina", "melton", "mercer", "merchant", "meredith",
    "meyer", "meyers", "miles", "miller", "mills", "mitchell", "montgomery", "moody",
    "moon", "mooney", "moore", "moran", "morgan", "morris", "morrison", "morton",
    "moss", "mueller", "mullen", "murphy", "murray", "myers", "nash", "neal",
    "nelson", "newman", "newton", "nichols", "nicholson", "noble", "nolan", "norman",
    "norris", "norton", "o'brien", "o'connor", "o'donnell", "o'neill", "oakley",
    "oliver", "olsen", "olson", "osborne", "owen", "owens", "page", "palmer", "park",
    "parker", "parkinson", "parks", "parsons", "patel", "patrick", "patterson",
    "patton", "paul", "payne", "pearce", "pearson", "peck", "pena", "penn",
    "pennington", "perkins", "perry", "peters", "peterson", "phelps", "phillips",
    "pierce", "pike", "piper", "pitts", "plummer", "pollard", "pond", "poole",
    "pope", "porter", "potter", "powell", "power", "powers", "pratt", "preston",
    "price", "prince", "pritchard", "proctor", "pugh", "quinn", "ramos", "randall",
    "ray", "raymond", "reed", "reid", "reilly", "reynolds", "rhodes", "rice",
    "richards", "richardson", "richmond", "riley", "ritchie", "rivera", "robbins",
    "roberts", "robertson", "robinson", "robson", "rodgers", "rogers", "rollins",
    "roman", "rose", "ross", "rowe", "rowland", "roy", "rush", "russell", "ryan",
    "sage", "sanders", "sanderson", "sanford", "saunders", "savage", "sawyer",
    "schmidt", "schofield", "scott", "sexton", "sharp", "shaw", "sheffield",
    "sheldon", "shepherd", "sherman", "shields", "short", "silva", "simmons",
    "simon", "simpson", "sinclair", "singh", "skinner", "slater", "sloan", "smart",
    "smith", "snyder", "solomon", "sparks", "spears", "spence", "spencer", "stanley",
    "stanton", "stark", "steele", "stephens", "stephenson", "stevens", "stevenson",
    "stewart", "stone", "stout", "strange", "strong", "stuart", "sullivan",
    "summers", "sutton", "swanson", "swift", "sykes", "tanner", "tate", "taylor",
    "temple", "terry", "thomas", "thompson", "thomson", "thornton", "thorpe",
    "tillman", "todd", "townsend", "tracy", "travis", "tucker", "turner", "tyler",
    "tyson", "underwood", "vaughan", "vaughn", "vincent", "wade", "wagner", "walker",
    "wallace", "walsh", "walters", "walton", "ward", "warner", "warren", "waters",
    "watkins", "watson", "watts", "weaver", "webb", "weber", "webster", "weeks",
    "wells", "welsh", "west", "wheeler", "whitaker", "white", "whitehead", "whitney",
    "wiggins", "wilcox", "wilder", "wiley", "wilkins", "wilkinson", "williams",
    "williamson", "willis", "wilson", "winter", "winters", "wise", "wolf", "wolfe",
    "wong", "wood", "woodard", "woods", "wright", "wyatt", "yates", "york", "young"
]

class NameGenerator:
    """Class to handle name generation with controlled uniqueness."""
    
    def __init__(self, unique_probability=0.98):
        """Initialize the name generator.
        
        Args:
            unique_probability (float): Probability of generating a unique last name
        """
        self.used_last_names = set()
        self.used_full_names = set()
        self.unique_probability = unique_probability
        self.available_names = LAST_NAMES.copy()
        random.shuffle(self.available_names)  # Randomize initial order
        
    def generate_name(self):
        """Generate a fake carrier name in 'lastname, f' format with controlled uniqueness."""
        while True:
            # Decide whether to enforce uniqueness for this name
            enforce_unique = random.random() < self.unique_probability
            
            if enforce_unique and self.available_names:
                # Use a name from our shuffled list of unused names
                last_name = self.available_names.pop()
            else:
                # Randomly select any name when we either don't need uniqueness
                # or have run out of unique names
                last_name = random.choice(LAST_NAMES)
            
            # Generate first initial
            first_initial = random.choice(string.ascii_lowercase)
            full_name = f"{last_name}, {first_initial}"
            
            # Check if this exact full name is unique
            if full_name not in self.used_full_names:
                self.used_last_names.add(last_name)
                self.used_full_names.add(full_name)
                return full_name

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

        # Create name mapping using the new NameGenerator
        name_generator = NameGenerator(unique_probability=0.98)
        name_mapping = {}
        for name in real_names:
            name_mapping[name] = name_generator.generate_name()

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
            
            # Add statistics about name uniqueness
            total_names = len(name_mapping)
            unique_last_names = len(set(fake.split(',')[0] for fake in name_mapping.values()))
            uniqueness_percentage = (unique_last_names / total_names) * 100
            
            f.write(f"\nName Generation Statistics:\n")
            f.write("========================\n")
            f.write(f"Total names generated: {total_names}\n")
            f.write(f"Unique last names: {unique_last_names}\n")
            f.write(f"Last name uniqueness: {uniqueness_percentage:.1f}%\n")

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
    parser = argparse.ArgumentParser(description="Sanitize a database by anonymizing sensitive data.")
    parser.add_argument("input_db", help="Path to the input database file")
    parser.add_argument(
        "output_db",
        help="Path where the sanitized database will be saved",
    )
    
    args = parser.parse_args()
    
    print(f"Input database: {args.input_db}")
    print(f"Output will be saved to: {args.output_db}")
    
    try:
        sanitize_database(args.input_db, args.output_db)
    except FileNotFoundError:
        print(f"Error: Input database '{args.input_db}' not found.")
        exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)
