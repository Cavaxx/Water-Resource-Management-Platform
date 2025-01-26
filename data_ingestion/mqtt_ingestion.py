import os
import json
import logging
import paho.mqtt.client as mqtt
from pymongo import MongoClient

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

MONGO_URI    = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
MQTT_BROKER  = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT    = int(os.getenv("MQTT_PORT", 1883))
TOPIC_LIST   = os.getenv("TOPICS", "city/water_facilities,sensors_data/river,weather_data/city,SPET/PET/city")
TOPICS       = [t.strip() for t in TOPIC_LIST.split(",") if t.strip()]

# ------------------------------------------------------------------------------
# Database Setup
# ------------------------------------------------------------------------------
mongo_client = MongoClient(MONGO_URI)
db           = mongo_client["water_management"]

def create_collection_if_not_exists(db, collection_name):
    """
    Create the specified collection if it doesn't already exist.
    This function will do nothing if the collection exists.
    """
    existing_collections = db.list_collection_names()
    if collection_name not in existing_collections:
        db.create_collection(collection_name)
        logging.info(f"Collection '{collection_name}' created successfully in database '{db.name}'.")
    else:
        logging.info(f"Collection '{collection_name}' already exists in database '{db.name}'.")

# ------------------------------------------------------------------------------
# MQTT Callbacks
# ------------------------------------------------------------------------------
def on_connect(client, userdata, flags, rc):
    """Callback when the client connects to the broker."""
    if rc == 0:
        logging.info("Connected to MQTT broker successfully.")
        # Subscribe to all relevant topics
        for topic in TOPICS:
            client.subscribe(topic)
            logging.info(f"Subscribed to topic: {topic}")
    else:
        logging.error(f"Failed to connect to MQTT broker. Return code: {rc}")

def on_message(client, userdata, message):
    """Callback when a message is received from the broker."""
    topic = message.topic
    try:
        payload = json.loads(message.payload.decode("utf-8"))
    except json.JSONDecodeError:
        logging.warning(f"Received invalid JSON on topic '{topic}': {message.payload}")
        return

    logging.info(f"Received message on topic '{topic}': {payload}")

    # Determine which collection to insert data into
    if topic == "city/water_facilities":
        collection_name = "water_facilities"
    elif topic == "sensors_data/river":
        collection_name = "sensor_data"
    elif topic == "weather_data/city":
        collection_name = "weather_data"
    elif topic == "SPET/PET/city":
        collection_name = "spei_pet"
    else:
        logging.warning(f"Unhandled topic: {topic}")
        return

    # Create the collection if it doesn't exist yet
    create_collection_if_not_exists(db, collection_name)
    collection = db[collection_name]

    # Insert into MongoDB
    try:
        collection.insert_one(payload)
        logging.info(f"Inserted document into '{collection.name}': {payload}")
    except Exception as e:
        logging.error(f"Error inserting document into '{collection.name}': {e}")

# ------------------------------------------------------------------------------
# Main Service Loop
# ------------------------------------------------------------------------------
def main():
    """Main entrypoint for the MQTT ingestion service."""
    mqtt_client = mqtt.Client()

    # Set up MQTT callbacks
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    # Connect to MQTT Broker
    logging.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

    # Start the loop
    logging.info("MQTT Ingestion Service is running...")
    mqtt_client.loop_forever()

if __name__ == "__main__":
    main()
