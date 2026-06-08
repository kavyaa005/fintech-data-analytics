"""
=============================================================================
 Bluestock Fintech Internship — Day 1
 File   : live_nav_fetch.py
 Purpose: Fetch live NAV data from mfapi.in for 6 large-cap equity schemes,
          parse JSON responses, and save each as a raw CSV.
=============================================================================
"""

import os
import time
import json
import requests
import pandas as pd
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
RAW_DIR  = os.path.join("data", "raw")
BASE_URL = "https://api.mfapi.in/mf/{amfi_code}"

SCHEMES = {
    125497: "HDFC Top 100 Direct",
    119551: "SBI Bluechip Direct",
    120503: "ICICI Prudential Bluechip Direct",
    118632: "Nippon India Large Cap Direct",
    119092: "Axis Bluechip Direct",
    120841: "Kotak Bluechip Direct",
}

SEP = "=" * 72

# ── Helpers ───────────────────────────────────────────────────────────────────
def _banner(msg: str) -> None:
    print(f"\n{SEP}\n  {msg}\n{SEP}")


def fetch_nav(amfi_code: int, scheme_name: str) -> pd.DataFrame | None:
    """Fetch NAV history for a single scheme and return as DataFrame."""
    url = BASE_URL.format(amfi_code=amfi_code)
    print(f"\n  ▶  [{amfi_code}] {scheme_name}")
    print(f"     URL : {url}")

    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.ConnectionError:
        print("     ✖  Network error — check internet connection.")
        return None
    except requests.exceptions.Timeout:
        print("     ✖  Request timed out after 15 s.")
        return None
    except requests.exceptions.HTTPError as exc:
        print(f"     ✖  HTTP {exc.response.status_code}")
        return None
    except json.JSONDecodeError:
        print("     ✖  Could not parse JSON response.")
        return None

    # ── Parse ──────────────────────────────────────────────────────────────
    meta   = data.get("meta", {})
    nav_data = data.get("data", [])

    if not nav_data:
        print("     ⚠  Empty 'data' array in response.")
        return None

    df = pd.DataFrame(nav_data)                       # columns: date, nav
    df.rename(columns={"date": "nav_date", "nav": "nav_value"}, inplace=True)
    df["nav_date"]   = pd.to_datetime(df["nav_date"], format="%d-%m-%Y", dayfirst=True)
    df["nav_value"]  = pd.to_numeric(df["nav_value"], errors="coerce")
    df["amfi_code"]  = amfi_code
    df["scheme_name"]= scheme_name
    df["fund_house"] = meta.get("fund_house", "")
    df["scheme_type"]= meta.get("scheme_type", "")
    df["scheme_category"] = meta.get("scheme_category", "")
    df["fetched_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    df.sort_values("nav_date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # ── Save ───────────────────────────────────────────────────────────────
    os.makedirs(RAW_DIR, exist_ok=True)
    safe_name = scheme_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
    out_path  = os.path.join(RAW_DIR, f"nav_{amfi_code}_{safe_name}.csv")
    df.to_csv(out_path, index=False)

    print(f"     ✔  {len(df):,} records fetched")
    print(f"        Date range : {df['nav_date'].min().date()}  →  {df['nav_date'].max().date()}")
    print(f"        Latest NAV : ₹ {df['nav_value'].iloc[-1]:.4f}")
    print(f"        Saved to   : {out_path}")
    return df


# ── Main ──────────────────────────────────────────────────────────────────────
def fetch_all_nav() -> dict[int, pd.DataFrame]:
    _banner("Bluestock Fintech — Day 1 : Live NAV Fetch  (mfapi.in)")
    print(f"  Schemes to fetch : {len(SCHEMES)}")
    print(f"  Output directory : {RAW_DIR}/")

    results: dict[int, pd.DataFrame] = {}
    failed:  list[int]               = []

    for amfi_code, scheme_name in SCHEMES.items():
        df = fetch_nav(amfi_code, scheme_name)
        if df is not None:
            results[amfi_code] = df
        else:
            failed.append(amfi_code)
        time.sleep(0.5)   # polite delay between API calls

    # ── Consolidated file ──────────────────────────────────────────────────
    if results:
        all_nav = pd.concat(results.values(), ignore_index=True)
        consolidated_path = os.path.join(RAW_DIR, "nav_all_schemes.csv")
        all_nav.to_csv(consolidated_path, index=False)
        print(f"\n  ✔  Consolidated file  : {consolidated_path}  ({len(all_nav):,} total rows)")

    # ── Summary ────────────────────────────────────────────────────────────
    _banner("Fetch Summary")
    print(f"  ✔  Succeeded : {len(results)} / {len(SCHEMES)} schemes")
    if failed:
        print(f"  ✖  Failed    : {failed}")

    return results


if __name__ == "__main__":
    nav_data = fetch_all_nav()
    print("\n  ✔  live_nav_fetch.py finished successfully.\n")
