import pandas as pd
import requests
import time
import os
from datetime import datetime

API_URL = os.getenv("API_URL", "http://localhost:8000")

df = pd.read_csv("data/IoT_Indoor_Air_Quality_Dataset.csv")
df = df.fillna(0)  # add this line
print(f"Loaded {len(df)} rows of IoT sensor data")
print("Starting IoT simulator... Press Ctrl+C to stop.")


for index, row in df.iterrows():
    payload = {
        "device_id": f"sensor_{index % 50 + 1:02d}",
        "timestamp": str(row['Timestamp']),
        "temperature": float(row['Temperature (?C)']),
        "humidity": float(row['Humidity (%)']),
        "co2": float(row['CO2 (ppm)']),
        "pm25": float(row['PM2.5 (?g/m?)']),
        "pm10": float(row['PM10 (?g/m?)']),
        "tvoc": float(row['TVOC (ppb)']),
        "co": float(row['CO (ppm)']),
        "light": float(row['Light Intensity (lux)']),
        "motion": int(row['Motion Detected']),
        "occupancy": int(row['Occupancy Count']),
    }

    try:
        response = requests.post(f"{API_URL}/ingest", json=payload)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Sent sensor_{index % 50 + 1:02d} → Status: {response.status_code}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] FastAPI not running yet: {e}")

    time.sleep(0.5)  # Adjust the sleep time as needed to control the data sending rate

print("Dataset finished! Restarting...") 	