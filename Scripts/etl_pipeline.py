import pandas as pd
import sqlite3
from pathlib import Path

RAW_DIR = Path("Data/raw")
DB_PATH = Path("Data/db/bluestock_mf.db")

conn = sqlite3.connect(DB_PATH)

for csv_file in RAW_DIR.glob("*.csv"):

    table_name = csv_file.stem.lower()

    print(f"Loading {csv_file.name}")

    df = pd.read_csv(csv_file)

    df.to_sql(
        table_name,
        conn,
        if_exists="replace",
        index=False
    )

print("\nAll files loaded successfully.")

conn.close()