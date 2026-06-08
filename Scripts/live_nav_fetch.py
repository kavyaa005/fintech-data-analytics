import requests
import pandas as pd

url = "https://api.mfapi.in/mf/125497"

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()
    nav_df = pd.DataFrame(data["data"])

    nav_df.to_csv(
        r"C:\Users\Dell\OneDrive\Desktop\Fintech_Data_Analytics\Data\raw\live_nav_hdfc.csv",
        index=False
    )

    print(nav_df.head())

except requests.exceptions.RequestException as e:
    print("Error fetching data:", e)