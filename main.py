import json
import time
import random
from datetime import datetime, timezone
from pysolar.solar import get_altitude, get_azimuth
import matplotlib.pyplot as plt
import serial

COORDS_FILE = "coords.json"
SERIAL_PORT = 'COM3'    
BAUD_RATE = 9600

def load_coords():
    try:
        with open(COORDS_FILE, "r") as f:
            data = json.load(f)
            return data["latitude"], data["longitude"]
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return 16.6267, -93.1002  # Default coordinates

def setup_serial():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(0.5)  
    return ser

def get_sun_angles(lat, lon):
    date_time_utc = datetime.now(timezone.utc)
    elevation_deg = get_altitude(lat, lon, date_time_utc)
    azimuth_deg = get_azimuth(lat, lon, date_time_utc)

    zenith_deg = 90 - elevation_deg
    azimuth_deg = max(0, min(180, azimuth_deg))
    zenith_deg = max(0, min(180, zenith_deg))

    return azimuth_deg, zenith_deg

def genetic_algorithm():
    ser = setup_serial()
    
    lat, lon = load_coords()
    print(f"Using Latitude: {lat}, Longitude: {lon}")

    target_azimuth, target_zenith = get_sun_angles(lat, lon)
    print(f"Sun Azimuth: {target_azimuth:.2f}, Zenith: {target_zenith:.2f}")

    ser.close()

if __name__ == "__main__":
    genetic_algorithm()
