import os
import json
import requests
import logging
import time
import schedule
import paho.mqtt.client as mqtt
from datetime import datetime

# ------------------------------------------------------------------------------
# Logging Setup
# ------------------------------------------------------------------------------
logging.basicConfig(
    filename='weather_data_fetcher.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# ------------------------------------------------------------------------------
# MQTT Configuration
# ------------------------------------------------------------------------------
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = "weather_data/city"  # Publish weather data here

mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

# ------------------------------------------------------------------------------
# Weather API Setup
# ------------------------------------------------------------------------------
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")  # Ensure your API key is set via environment variable

# ------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------
def publish_weather_data(weather_data):
    """
    Build a document from the weather data and publish it to MQTT.
    
    Args:
        weather_data (dict): The raw JSON response from OpenWeatherMap API.
    """
    try:
        # Extract relevant fields
        document = {
            "city": weather_data.get("name"),
            "coordinates": weather_data.get("coord"),
            "weather": weather_data.get("weather", [{}])[0],  # Weather condition (assuming only one)
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

        # Convert the document to JSON
        payload = json.dumps(document)

        # Publish to MQTT
        result = mqtt_client.publish(MQTT_TOPIC, payload)
        if result.rc == 0:
            logging.info(f"Weather data for {weather_data.get('name')} published to '{MQTT_TOPIC}'.")
        else:
            logging.error(f"Failed to publish weather data. MQTT result code: {result.rc}")

    except Exception as e:
        logging.error(f"Failed to publish weather data: {e}")

def fetch_weather_data_current(location, api_key=WEATHER_API_KEY):
    """
    Fetch current weather data for a specific city and publish via MQTT.
    """
    if not api_key:
        logging.error("WEATHER_API_KEY environment variable not set.")
        return
    
    WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': location,
        'appid': api_key,
        'units': 'metric'
    }
    try:
        response = requests.get(WEATHER_API_URL, params=params)
        if response.status_code == 200:
            weather_data = response.json()
            publish_weather_data(weather_data)  # Publish to MQTT instead of MongoDB
            logging.info(f"Successfully fetched weather data for {location}.")
        else:
            logging.error(f"Failed to fetch data for {location}. Status code: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error fetching weather data for {location}: {e}")

def fetch_and_publish_weather_data():
    """
    Fetch and publish weather data for a list of Trentino cities.
    """
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
    # Run immediately at startup
    fetch_and_publish_weather_data()

    # Schedule the job to run every 24 hours
    schedule.every(24).hours.do(fetch_and_publish_weather_data)

    # Alternatively, you could schedule the job to run at a specific time:
    # schedule.every().day.at("06:00").do(fetch_and_publish_weather_data)

    logging.info("Scheduler started. The script will fetch weather data every 24 hours.")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
