import json
import random
import time
import numpy as np
from pymongo import MongoClient

# MongoDB connection details
MONGO_URI = "mongodb://mongo:27017/"
DB_NAME = "water_management"
COLLECTION_NAME = "synthetic_weather_data"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Generate synthetic weather data
current_timestamp = int(time.time())

cities = ["Trento", "Rovereto", "Pergine Valsugana", "Arco", "Riva del Garda"]
coordinates = {
    "Trento": {"lon": 11.1211, "lat": 46.0679},
    "Rovereto": {"lon": 11.0387, "lat": 45.8896},
    "Pergine Valsugana": {"lon": 11.238, "lat": 46.065},
    "Arco": {"lon": 10.8867, "lat": 45.9177},
    "Riva del Garda": {"lon": 10.8412, "lat": 45.8858},
}

# Parameters for data generation
num_days = 100
weather_conditions = ["Clear", "Clouds", "Rain", "Drizzle", "Snow"]
mean_temp = 15
mean_rainfall = 2

synthetic_data = []

for city in cities:
    for day in range(num_days):
        weather_main = random.choice(weather_conditions)
        weather_entry = {
            "id": random.randint(800, 804),
            "main": weather_main,
            "description": f"{weather_main.lower()} sky",
            "icon": "01n" if weather_main == "Clear" else "04n",
        }

        temp = round(random.gauss(mean_temp, 5), 2)
        temp_min = round(temp - random.uniform(0, 5), 2)
        temp_max = round(temp + random.uniform(0, 5), 2)
        feels_like = round(temp - random.uniform(0, 3), 2)
        pressure = random.randint(980, 1030)  # hPa
        humidity = random.randint(30, 100)  # %
        clouds = random.randint(0, 100)  # %

        # Wind as dict
        wind_entry = {
            "speed": round(random.uniform(0, 15), 2),  # m/s
            "deg": random.randint(0, 360),             # degrees
            "gust": round(random.uniform(0, 5), 2)
        }

        # Rain as dict
        rain_entry = {"1h": round(np.random.gamma(2, mean_rainfall / 2), 2)} if weather_main in ["Rain", "Drizzle"] else {"1h": 0.0}

        # Sunrise and Sunset
        sunrise = current_timestamp - day * 86400 + random.randint(21600, 25200)  # 6-7 AM
        sunset = current_timestamp - day * 86400 + random.randint(64800, 68400)   # 6-7 PM

        # Synthetic weather entry matching schema
        synthetic_entry = {
            "city": city,
            "coordinates": coordinates[city],
            "weather": weather_entry,
            "temperature": temp,
            "feels_like": feels_like,
            "temp_min": temp_min,
            "temp_max": temp_max,
            "pressure": pressure,
            "humidity": humidity,
            "wind": wind_entry,
            "rain": rain_entry,
            "clouds": clouds,
            "sunrise": sunrise,
            "sunset": sunset,
            "timestamp": current_timestamp - day * 86400,
        }

        synthetic_data.append(synthetic_entry)

# Insert synthetic data into MongoDB
collection.delete_many({})  # Clear old data
collection.insert_many(synthetic_data)
print(f"Inserted {len(synthetic_data)} records into the '{COLLECTION_NAME}' collection.")


