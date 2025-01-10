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
weather_descriptions = {
    "Clear": "clear sky",
    "Clouds": "overcast clouds",
    "Rain": "light rain",
    "Drizzle": "light intensity drizzle",
    "Snow": "light snow",
}
weather_icons = {
    "Clear": "01n",
    "Clouds": "04n",
    "Rain": "10n",
    "Drizzle": "09n",
    "Snow": "13n",
}
mean_temp = 15  # Average temperature in Celsius
mean_rainfall = 2  # Average rainfall in mm

synthetic_data = []

for city in cities:
    for day in range(num_days):
        weather_main = random.choice(weather_conditions)
        weather_desc = weather_descriptions[weather_main]
        weather_icon = weather_icons[weather_main]
        weather_id = random.randint(800, 804) if weather_main != "Snow" else random.randint(600, 622)

        temp = round(random.gauss(mean_temp, 5), 2)
        temp_min = round(temp - random.uniform(0, 5), 2)
        temp_max = round(temp + random.uniform(0, 5), 2)
        feels_like = round(temp - random.uniform(0, 3), 2)
        pressure = random.randint(980, 1030)  # in hPa
        humidity = random.randint(30, 100)  # in %
        wind_speed = round(random.uniform(0, 15), 2)  # in m/s
        wind_deg = random.randint(0, 360)  # in degrees
        wind_gust = round(wind_speed + random.uniform(0, 5), 2) if wind_speed > 5 else 0.0
        rain_volume = round(np.random.gamma(2, mean_rainfall / 2), 2) if weather_main in ["Rain", "Drizzle"] else 0.0
        clouds = random.randint(0, 100)  # in %
        sunrise = current_timestamp - day * 86400 + random.randint(20000, 30000)  # Synthetic sunrise timestamp
        sunset = current_timestamp - day * 86400 + random.randint(60000, 70000)  # Synthetic sunset timestamp

        synthetic_entry = {
            "city": city,
            "coordinates": coordinates[city],
            "weather": {
                "id": weather_id,
                "main": weather_main,
                "description": weather_desc,
                "icon": weather_icon
            },
            "temperature": temp,
            "feels_like": feels_like,
            "temp_min": temp_min,
            "temp_max": temp_max,
            "pressure": pressure,
            "humidity": humidity,
            "wind": {
                "speed": wind_speed,
                "deg": wind_deg,
                "gust": wind_gust
            },
            "rain": {
                "1h": rain_volume
            },
            "clouds": clouds,
            "sunrise": sunrise,
            "sunset": sunset,
            "timestamp": current_timestamp - day * 86400,
        }
        synthetic_data.append(synthetic_entry)

# Insert synthetic data into MongoDB
collection.insert_many(synthetic_data)
print(f"Inserted {len(synthetic_data)} records into the '{COLLECTION_NAME}' collection.")

