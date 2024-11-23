import os
import requests
import logging
from pymongo import MongoClient
from datetime import datetime

# Setup logging
logging.basicConfig(filename='weather_data_fetcher.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
client = MongoClient(MONGO_URI)
db = client["water_management"]
weather_collection = db["weather_data"]

##########################################################
#######   MODIFY THE FOLLOWING PART  #####################
##########################################################
# Weather API setup
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")  # Store your API key as an environment variable
WEATHER_API_URL = "https://api.weatherapi.com/v1/history.json"  # Example API endpoint
LOCATION = os.getenv("LOCATION", "London")  # Default location

def fetch_weather_data(date):
    """
    Fetch historical weather data for a specific date.
    """
    try:
        params = {
            "key": WEATHER_API_KEY,
            "q": LOCATION,
            "dt": date
        }
        response = requests.get(WEATHER_API_URL, params=params)
        if response.status_code == 200:
            weather_data = response.json()
            store_weather_data(weather_data)
        else:
            logging.error(f"Failed to fetch data for {date}. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error fetching weather data: {e}")

def store_weather_data(data):
    """
    Process and store weather data in the MongoDB collection.
    """
    try:
        weather_record = {
            "location": data.get("location", {}).get("name"),
            "region": data.get("location", {}).get("region"),
            "country": data.get("location", {}).get("country"),
            "date": data.get("forecast", {}).get("forecastday", [{}])[0].get("date"),
            "daily_data": data.get("forecast", {}).get("forecastday", [{}])[0].get("day")
        }
        weather_collection.update_one(
            {"date": weather_record["date"], "location": weather_record["location"]},
            {"$set": weather_record},
            upsert=True
        )
        logging.info(f"Successfully stored weather data for {weather_record['date']}")
    except Exception as e:
        logging.error(f"Error storing weather data: {e}")

def main():
    # Example: Fetch weather data for the last 7 days
    from datetime import timedelta
    today = datetime.now()
    for i in range(7):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        fetch_weather_data(date)

if __name__ == "__main__":
    main()
