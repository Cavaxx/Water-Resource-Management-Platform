import os
import json
import requests
import logging
import paho.mqtt.client as mqtt

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# URL to fetch the JSON data
URL = "https://telecontrollo.cliquenet.it/opendata/siti"

# Keys to extract from the JSON
KEYS = [
    "id_sito", 
    "indirizzo", 
    "comune", 
    "comuni_serviti", 
    "descrizione", 
    "longitude", 
    "latitude", 
    "altezza_mslm", 
    "nome", 
    "recettore"
]

# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT   = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC  = "city/water_facilities"  # The topic on which to publish

# ------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------
def fetch_json_data(url):
    """Fetch JSON data from the given URL and return it as a Python list/dict."""
    logging.info(f"Fetching JSON data from: {url}")
    response = requests.get(url)
    response.raise_for_status()  # Raise if the request failed
    return response.json()

def process_data_and_publish(json_data, mqtt_client, topic):
    """
    Extract specific keys from each item in the JSON data and publish 
    the resulting document to a given MQTT topic.
    """
    if not isinstance(json_data, list):
        logging.warning("Unexpected JSON format. Expected a list of items.")
        return

    for item in json_data:
        # Build a document with the required keys
        document = {key: item.get(key, "") for key in KEYS}

        # Convert to JSON for publishing
        payload_str = json.dumps(document)
        
        # Publish to MQTT
        result = mqtt_client.publish(topic, payload_str)

        if result.rc == 0:
            logging.info(f"Published to '{topic}': {document}")
        else:
            logging.error(f"Failed to publish to '{topic}'. Result code: {result.rc}")

# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
def main():
    # 1. Fetch JSON data
    json_data = fetch_json_data(URL)

    # 2. Set up the MQTT client
    mqtt_client = mqtt.Client()
    logging.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

    # 3. Process the data and publish to MQTT
    process_data_and_publish(json_data, mqtt_client, MQTT_TOPIC)
    
    # 4. (Optional) Disconnect cleanly
    mqtt_client.disconnect()
    logging.info("Done. Disconnected from MQTT broker.")

if __name__ == "__main__":
    main()