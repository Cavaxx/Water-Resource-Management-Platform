import json
import math

# Function to calculate daylight hours
def calculate_daylight_hours(latitude, day_of_year):
    # Convert latitude to radians
    phi = math.radians(latitude)
    
    # Calculate declination (in radians)
    declination = math.radians(23.45 * math.sin(math.radians((360 / 365) * (day_of_year - 81))))
    
    # Calculate hour angle (H) in radians
    hour_angle = math.acos(-math.tan(phi) * math.tan(declination))
    
    # Convert hour angle to daylight hours (L)
    daylight_hours = (2 * math.degrees(hour_angle)) / 15
    return daylight_hours

# Load synthetic weather data
file_path = "/home/pariamelle/BDT_project/Water-Resource-Management-Platform/data_management/synthetic_weather_data.json"

# Open and read the JSON file
with open(file_path, "r") as file:
    synthetic_weather_data = json.load(file)

# Group data by city
city_data = {}
for entry in synthetic_weather_data:
    city_name = entry["city"]
    if city_name not in city_data:
        city_data[city_name] = {
            "T_min": [],
            "T_max": [],
            "Humidity": [],
            "Latitude": entry["coordinates"]["lat"],  # Latitude should be same for all days in a city
            "Precipitations": [],
            "Day": [],
        }
    
    # Append weather data to the city's list
    city_data[city_name]["T_min"].append(entry["temp_min"])
    city_data[city_name]["T_max"].append(entry["temp_max"])
    city_data[city_name]["Humidity"].append(entry["humidity"])
    city_data[city_name]["Precipitations"].append(entry["rain"])
    city_data[city_name]["Day"].append(entry["timestamp"])

# Iterate over each city and compute the metrics
for city_name, data in city_data.items():
    T_min = data["T_min"]
    T_max = data["T_max"]
    Humidity = data["Humidity"]
    Latitude = data["Latitude"]
    Precipitations = data["Precipitations"]
    Day = data["Day"]
    
    # Calculate number of days
    N = len(T_min)

    # Calculate the daily mean temperature (T)
    T = sum([(tmin + tmax) / 2 for tmin, tmax in zip(T_min, T_max)]) / N

    # Calculate daylight hours (L) using the first available day from the data
    day_of_year = (Day[0] - 1732894969) // (24 * 3600) + 1  # Adjust based on the timestamp base
    L = calculate_daylight_hours(Latitude, day_of_year)

    # Calculate Heat Index (I) and exponent (a) for Thornthwaite method
    I = 20.35  # This value can be adjusted or computed
    a = 6.75 * 10**-7 * I**3 - 7.71 * 10**-5 * I**2 + 1.79 * 10**-2 * I + 0.49239

    # Calculate daily PET (Potential Evapotranspiration)
    PET_m = 16 * L / 12 * (10 * T / I) ** a

    # Calculate total precipitation
    P_m = sum(Precipitations)

    # Calculate Drought Measure
    DM_T = P_m - PET_m

    # Simplified SPEI (not standardized, just as a placeholder)
    SPEI_T = DM_T  # Note: This is NOT a standardized SPEI value

    # Print the results for the current city
    print(f"City: {city_name}")
    print(f"Daylight hours: {L:.2f} hours")
    print(f"Total Precipitation (P_m): {P_m:.2f} mm")
    print(f"Total PET (PET_m): {PET_m:.2f} mm")
    print(f"Drought Measure (DM_T): {DM_T:.2f} mm")
    print(f"Simplified SPEI-T: {SPEI_T:.2f} mm")
    print("-" * 40)
