import pandas as pd
import os

data_folder = "Data/raw"

print("Reading CSV files...\n")

if not os.path.exists(data_folder):
    print(f"Folder not found: {data_folder}")
else:
    files = os.listdir(data_folder)

    for file in files:
        if file.endswith(".csv"):
            path = os.path.join(data_folder, file)

            print("=" * 50)
            print("FILE:", file)

            df = pd.read_csv(path)

            print("Rows, Columns:", df.shape)

            print("\nColumn Names:")
            print(df.columns.tolist())

            print("\nData Types:")
            print(df.dtypes)

            print("\nFirst 5 Rows:")
            print(df.head())

            print("\nMissing Values:")
            print(df.isnull().sum())

            print("\n")