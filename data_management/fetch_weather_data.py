import os
import requests
import logging
from pymongo import MongoClient
from datetime import datetime
import time
import schedule

# Setup logging
logging.basicConfig(filename='weather_data_fetcher.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
client = MongoClient(MONGO_URI)
db = client["water_management"]
weather_collection = db["weather_data"]

# Weather API setup
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")  # Store your API key as an environment variable

def store_weather_data(weather_data):
    """
    Store weather data into the MongoDB collection.

    Args:
        weather_data (dict): The weather data JSON response from the API.
    """
    try:
        # Extract relevant fields
        document = {
            "city": weather_data.get("name"),
            "coordinates": weather_data.get("coord"),
            "weather": weather_data.get("weather")[0],  # Assuming only one weather condition
            "temperature": weather_data.get("main", {}).get("temp"),
            "feels_like": weather_data.get("main", {}).get("feels_like"),
            "temp_min": weather_data.get("main", {}).get("temp_min"),
            "temp_max": weather_data.get("main", {}).get("temp_max"),
            "pressure": weather_data.get("main", {}).get("pressure"),
            "humidity": weather_data.get("main", {}).get("humidity"),
            "wind": weather_data.get("wind"),
            "rain": weather_data.get("rain", {}),
            "clouds": weather_data.get("clouds", {}).get("all"),
            "sunrise": weather_data.get("sys", {}).get("sunrise"),
            "sunset": weather_data.get("sys", {}).get("sunset"),
            "timestamp": weather_data.get("dt")
        }

        # Insert into MongoDB
        result = weather_collection.insert_one(document)
        logging.info(f"Weather data for {weather_data.get('name')} inserted with ID: {result.inserted_id}")

    except Exception as e:
        logging.error(f"Failed to store weather data: {e}")

def fetch_weather_data_current(location, api_key=WEATHER_API_KEY):
    """
    Fetch current weather data for a specific city.
    """
    if not api_key:
        logging.error("WEATHER_API_KEY environment variable not set.")
        return
    WEATHER_API_URL = f"http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': location,
        'appid': api_key,
        'units': 'metric'
    }
    try:
        response = requests.get(WEATHER_API_URL, params=params)
        if response.status_code == 200:
            weather_data = response.json()
            store_weather_data(weather_data)  # Save to MongoDB
            logging.info(f"Successfully fetched weather data for {location}.")
        else:
            logging.error(f"Failed to fetch data for {location}. Status code: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error fetching weather data for {location}: {e}")

def fetch_and_store_weather_data():
    """
    Fetch and store weather data for a list of locations.
    """
    # List of locations (comuni_trentino)
    comuni_trentino = [
        "Trento",
        "Rovereto",
        "Pergine Valsugana",
        "Arco",
        "Riva del Garda",
        "Lavis",
        "Ala",
        "Mori",
        "Mezzolombardo",
        "Borgo Valsugana",
    ]
    logging.info("Starting weather data fetch for comuni_trentino.")
    for location in comuni_trentino:
        logging.info(f"Fetching weather data for {location}")
        fetch_weather_data_current(location)
        time.sleep(1)  # Sleep for 1 second to avoid hitting rate limits

def main():
    # Run the job immediately at startup
    fetch_and_store_weather_data()

    # Schedule the job to run every 24 hours
    schedule.every(24).hours.do(fetch_and_store_weather_data)

    # Alternatively, schedule the job to run at a specific time every day
    # schedule.every().day.at("06:00").do(fetch_and_store_weather_data)

    logging.info("Scheduler started. The script will fetch weather data every 24 hours.")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
