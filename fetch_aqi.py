import requests
import pandas as pd
import time
import os
from datetime import datetime, timedelta, timezone

# OpenWeatherMap API key
API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Karachi coordinates
LAT = 24.8607
LON = 67.0011

# File to store AQI data
CSV_FILE = "karachi_air_quality.csv"

def get_unix_timestamp(dt):
    return int(dt.timestamp())

def load_existing_timestamps():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        return set(df['timestamp'])  # already ISO format
    return set()

def fetch_aqi_data(start_time, end_time):
    url = f"http://api.openweathermap.org/data/2.5/air_pollution/history"
    params = {
        "lat": LAT,
        "lon": LON,
        "start": get_unix_timestamp(start_time),
        "end": get_unix_timestamp(end_time),
        "appid": API_KEY
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("list", [])

def main():
    # Set start date (permanent historical start)
    start_time = datetime(2025, 6, 1, tzinfo=timezone.utc)

    # End at current time (UTC-aware)
    end_time = datetime.now(timezone.utc)

    existing_timestamps = load_existing_timestamps()
    all_data = []

    while start_time < end_time:
        batch_end = min(start_time + timedelta(days=5), end_time)
        print(f"Fetching: {start_time} to {batch_end}")

        try:
            hourly_data = fetch_aqi_data(start_time, batch_end)
        except Exception as e:
            print(f"Error fetching data: {e}")
            break

        for entry in hourly_data:
            ts_dt = datetime.fromtimestamp(entry["dt"], timezone.utc)
            ts = ts_dt.isoformat()

            if ts_dt > end_time or ts in existing_timestamps:
                continue  # skip future or duplicate data

            main_data = entry["main"]
            components = entry["components"]

            row = {
                "timestamp": ts,
                "aqi": main_data["aqi"],
                "co": components.get("co"),
                "no": components.get("no"),
                "no2": components.get("no2"),
                "o3": components.get("o3"),
                "so2": components.get("so2"),
                "pm2_5": components.get("pm2_5"),
                "pm10": components.get("pm10"),
                "nh3": components.get("nh3"),
            }
            all_data.append(row)

        start_time = batch_end

    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(CSV_FILE, mode='a', index=False, header=not os.path.exists(CSV_FILE))
        print(f"Saved {len(all_data)} new records.")
    else:
        print("No new data to save.")

if __name__ == "__main__":
    main()
