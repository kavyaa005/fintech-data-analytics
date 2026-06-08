import requests
import pandas as pd

# 5 mutual fund scheme codes
codes = [
    119551,
    120503,
    118632,
    119092,
    120841
]

for code in codes:

    url = f"https://api.mfapi.in/mf/{code}"

    response = requests.get(url, timeout=10)

    if response.status_code == 200:

        data = response.json()

        df = pd.DataFrame(data["data"])

        file_path = rf"C:\Users\Dell\OneDrive\Desktop\Fintech_Data_Analytics\Data\raw\nav_{code}.csv"

        df.to_csv(file_path, index=False)

        print(f"Saved {code}")

    else:
        print(f"Failed for {code}")