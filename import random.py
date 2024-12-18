import json
import random

# Initialize a dictionary to store city data and calculate averages
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
                "wind": [],
                "rain":[]
            }

        # Append temperature data
        city_data[city_name]["temperatures"].append(data["temperature"])
        city_data[city_name]["feels_like"].append(data["feels_like"])
        city_data[city_name]["temp_min"].append(data["temp_min"])
        city_data[city_name]["temp_max"].append(data["temp_max"])
        city_data[city_name]["pressure"].append(data["pressure"])
        city_data[city_name]["humidity"].append(data["humidity"])
        city_data[city_name]["rain"].append(data["rain"])

# Generate synthetic data for each city
synthetic_data = []
for city_name, details in city_data.items():
    coordinates = details["coordinates"]
    temperatures = details["temperatures"]
    feels_like = details["feels_like"]
    temp_min = details["temp_min"]
    temp_max = details["temp_max"]
    pressure = details["pressure"]
    humidity = details["humidity"]
    rain = details["rain"]
    # Calculate the avg data for the city
    avg_temperature = sum(temperatures) / len(temperatures)
    avg_feels_like = sum(feels_like) / len(feels_like)
    avg_temp_incr = (sum(temp_max) / len(temp_max)) - avg_temperature
    avg_temp_decr = avg_temperature - (sum(temp_min) / len(temp_min))
    avg_pressure = sum(pressure) / len(pressure)
    avg_humidity = sum(humidity) / len(humidity)
    avg_speed = sum(details["wind"]) / len(details["wind"]) if details["wind"] else 0
    avg_gust = avg_speed * 1.5 
    avg_rain = #######

    # Generate 100 synthetic data points
    for _ in range(100):
        synthetic_entry = {
            "city": city_name,
            "coordinates": coordinates,
            "weather": {
                "id": random.choice([800, 801, 802, 803, 804]),
                "main": random.choice(["Clear", "Clouds", "Rain", "Drizzle", "Snow"]),
                "description": random.choice(["clear sky", "few clouds"] if "main" == "Clear" else
                                             ["few clouds", "scattered clouds", "broken clouds", "overcast clouds"]),
                #"icon": random.choice("10d"), #Not necessary
            "temperature": round(random.gauss(avg_temperature, 5), 2),  # Add some variation
            "feels_like": round(random.gauss(avg_feels_like,5),2),
            "temp_min": ("temperature" + round(random.gauss(avg_temp_incr,5),2)),
            "temp_max": ("temperature" - round(random.gauss(avg_temp_decr,5),2)),
            "pressure": round(random.gauss(avg_pressure,5),2),
            "humidity": round(random.gauss(avg_humidity,5),2),
            "wind": {"speed":round(random.gauss(avg_speed,5),2),"deg":random.uniform(0, 360) ,"gust":round(random.gauss(avg_gust,5),2)},
            "rain": 0 if "main" == "Clear" or "main" == "Clouds" else round(random.gauss(avg_rain, 5), 2)

            }
            
        }
        synthetic_data.append(synthetic_entry)

print(synthetic_data)
# Save synthetic data to a file
#with open("synthetic_weather_data.json", "w") as output_file:
#    json.dump(synthetic_data, output_file, indent=4)

#print("Synthetic data generation complete. Saved to 'synthetic_weather_data.json')