import pandas as pd
import requests
import time
from datetime import datetime, timezone, timedelta
import pytz
import schedule
import os
import logging
from concurrent.futures import ThreadPoolExecutor
import paho.mqtt.client as mqtt
import json

# Setup logging
logging.basicConfig(filename='water_management.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# CSV file path
csv_file_path = "Water-Resource-Management-Platform/data/index_of_sensors.csv"

# MQTT setup
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = "sensors_data/river"  # You can change this topic as needed

mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

def fetch_and_store_data():
    """Reads the CSV file, fetches data from the listed endpoints, and processes it."""
    try:
        if not os.path.isfile(csv_file_path):
            logging.error(f"CSV file '{csv_file_path}' not found.")
            return
        
        # Read CSV file
        df = pd.read_csv(csv_file_path)

        # Use ThreadPoolExecutor for parallel processing of endpoints
        with ThreadPoolExecutor(max_workers=10) as executor:
            for index, row in df.iterrows():
                endpoint_url = row[-2]  # Assuming the endpoint URL is in the second last column
                executor.submit(fetch_data_from_endpoint, row, endpoint_url)
                
    except Exception as e:
        logging.error(f"Error in fetch_and_store_data: {e}")

def fetch_data_from_endpoint(row, endpoint_url):
    """Fetch data from a given endpoint URL and process the JSON response."""
    try:
        response = requests.get(endpoint_url)
        if response.status_code == 200:
            json_data = response.json()
            process_json_data(json_data, row)
        else:
            logging.error(f"Failed to fetch data from {endpoint_url}, status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error fetching data from {endpoint_url}: {e}")

def process_json_data(json_data, row):
    """Iterate over the JSON data, extract relevant information, and forward for further processing."""
    try:
        for feature in json_data["features"]:
            properties = feature["properties"]

            # Retrieve additional data from the CSV
            latitude = row[0]
            longitude = row[1]
            site = row[2]
            water_body = row[3]
            uom = row[4]

            # Handle timestamp data
            timestamps_epoch = properties["data"]["timestamp"]
            values = properties["data"]["value"]

            # Ensure that timestamps and values are lists and have the same length
            if (isinstance(timestamps_epoch, list) and isinstance(values, list)
                    and len(timestamps_epoch) == len(values)):
                for timestamp_epoch, value in zip(timestamps_epoch, values):
                    process_and_publish_data(timestamp_epoch, value, latitude, longitude, site, water_body, uom)
            else:
                logging.warning(
                    f"Data format issue in {row[-2]}: timestamps and values are not lists or their lengths do not match."
                )
    except Exception as e:
        logging.error(f"Error processing JSON data: {e}")

def process_and_publish_data(timestamp_epoch, value, latitude, longitude, site, water_body, uom):
    """Convert epoch to human-readable timestamp, build a document, and publish it via MQTT."""
    try:
        # Convert epoch to UTC datetime
        timestamp_utc = datetime.utcfromtimestamp(timestamp_epoch).replace(tzinfo=timezone.utc)
        
        # Adjust to GMT +2 HOURS (Etc/GMT-2 means subtract 2 hours, so double-check if that's correct for your locale)
        timezone_adjusted = timestamp_utc.astimezone(pytz.timezone('Etc/GMT-2'))
        timestamp_human = timezone_adjusted.strftime('%Y-%m-%d %H:%M:%S')

        # Prepare document
        document = {
            "timestamp": timestamp_human,
            "value": value,
            "latitude": latitude,
            "longitude": longitude,
            "site": site,
            "water_body": water_body,
            "unit_of_measure": uom
        }

        # Publish the document to the MQTT topic
        mqtt_message = json.dumps(document)
        result = mqtt_client.publish(MQTT_TOPIC, mqtt_message)

        # Log the result
        if result.rc == 0:
            logging.info(f"Published data to MQTT topic '{MQTT_TOPIC}': {document}")
        else:
            logging.error(f"Failed to publish to MQTT topic '{MQTT_TOPIC}' with result code: {result.rc}")

    except Exception as e:
        logging.error(f"Error processing/publishing data: {e}")

# Schedule the job to run every 15 minutes
schedule.every(15).minutes.do(fetch_and_store_data)

# Run the job immediately at startup
fetch_and_store_data()

while True:
    schedule.run_pending()
    time.sleep(1)
