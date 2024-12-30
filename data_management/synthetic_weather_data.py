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
city_data = {}
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
        weather = random.choice(weather_conditions)
        temp = round(random.gauss(mean_temp, 5), 2)
        temp_min = round(temp - random.uniform(0, 5), 2)
        temp_max = round(temp + random.uniform(0, 5), 2)
        rain = round(np.random.gamma(2, mean_rainfall / 2), 2) if weather in ["Rain", "Drizzle"] else 0

        synthetic_entry = {
            "city": city,
            "coordinates": coordinates[city],
            "weather": weather,
            "temperature": temp,
            "temp_min": temp_min,
            "temp_max": temp_max,
            "rain": rain,
            "timestamp": current_timestamp - day * 86400,
        }
        synthetic_data.append(synthetic_entry)

# Insert synthetic data into MongoDB
collection.insert_many(synthetic_data)
print(f"Inserted {len(synthetic_data)} records into the '{COLLECTION_NAME}' collection.")

