import json
import random

# Initialize dictionaries for city data and summaries
city_data = {}
city_summaries = {}

# Read the JSON file and process data line by line
with open("data/weather_data.json", "r") as file:
    for line in file:
        data = json.loads(line)
        city_name = data["city"]
        coordinates = data["coordinates"]

        if city_name not in city_data:
            city_data[city_name] = {
                "coordinates": coordinates,
                "temperatures": [],
                "feels_like": [],
                "temp_min": [],
                "temp_max": [],
                "pressure": [],
                "humidity": [],
                #"rain": [],
                "wind": []
            }

        # Append weather data to the respective lists
        city_data[city_name]["temperatures"].append(data["temperature"])
        city_data[city_name]["feels_like"].append(data["feels_like"])
        city_data[city_name]["temp_min"].append(data["temp_min"])
        city_data[city_name]["temp_max"].append(data["temp_max"])
        city_data[city_name]["pressure"].append(data["pressure"])
        city_data[city_name]["humidity"].append(data["humidity"])
        #city_data[city_name]["rain"].append(data.get("rain", 0))  # Default rain to 0 if missing
        city_data[city_name]["wind"].append(data.get("wind_speed", 0))  # Default wind_speed to 0 if missing

# Generate city summaries (averages)
for city_name, details in city_data.items():
    city_summaries[city_name] = {
        "coordinates": details["coordinates"],
        "avg_temperature": sum(details["temperatures"]) / len(details["temperatures"]),
        "avg_feels_like": sum(details["feels_like"]) / len(details["feels_like"]),
        "avg_temp_min_deviation": (
            sum(details["temperatures"]) / len(details["temperatures"])
            - sum(details["temp_min"]) / len(details["temp_min"])
        ),
        "avg_temp_max_deviation": (
            sum(details["temp_max"]) / len(details["temp_max"])
            - sum(details["temperatures"]) / len(details["temperatures"])
        ),
        "avg_pressure": sum(details["pressure"]) / len(details["pressure"]),
        "avg_humidity": sum(details["humidity"]) / len(details["humidity"]),
        #"avg_rain": sum(details["rain"]) / len(details["rain"]) if details["rain"] else 0,
        "avg_wind_speed": sum(details["wind"]) / len(details["wind"]) if details["wind"] else 0
    }

# Generate synthetic data
synthetic_data = []
weather_descriptions = {
    "Clear": ["clear sky", "few clouds"],
    "Clouds": ["few clouds", "scattered clouds", "broken clouds", "overcast clouds"],
    "Rain": ["light rain", "moderate rain", "heavy intensity rain"],
    "Drizzle": ["light drizzle", "drizzle", "heavy drizzle"],
    "Snow": ["light snow", "snow", "heavy snow"]
}

for city_name, summary in city_summaries.items():
    for _ in range(100):
        weather_main = random.choice(list(weather_descriptions.keys()))
        description = random.choice(weather_descriptions[weather_main])

        synthetic_entry = {
            "city": city_name,
            "coordinates": summary["coordinates"],
            "weather": {
                "id": random.choice([800, 801, 802, 803, 804]),
                "main": weather_main,
                "description": description,
                "temperature": round(random.gauss(summary["avg_temperature"], 5), 2),
                "feels_like": round(random.gauss(summary["avg_feels_like"], 5), 2),
                "temp_min": round(random.gauss(summary["avg_temperature"] - summary["avg_temp_min_deviation"], 5), 2),
                "temp_max": round(random.gauss(summary["avg_temperature"] + summary["avg_temp_max_deviation"], 5), 2),
                "pressure": round(random.gauss(summary["avg_pressure"], 1), 2),
                "humidity": round(random.gauss(summary["avg_humidity"], 5), 2),
                "wind": {
                    "speed": round(random.gauss(summary["avg_wind_speed"], 5), 2),
                    "deg": random.uniform(0, 360),
                    "gust": round(random.gauss(summary["avg_wind_speed"] * 1.5, 5), 2)
                }
                #"rain": 0 if weather_main in ["Clear", "Clouds"] else round(random.gauss(summary["avg_rain"], 5), 2)
            }
        }
        synthetic_data.append(synthetic_entry)

# Print synthetic data for inspection
print(synthetic_data)

# Save synthetic data to a file
with open("synthetic_weather_data.json", "w") as output_file:
    json.dump(synthetic_data, output_file, indent=4)

print("Synthetic data generation complete. Saved to 'synthetic_weather_data.json'.")
