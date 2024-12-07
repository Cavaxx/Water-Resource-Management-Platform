import paho.mqtt.client as mqtt
from pymongo import MongoClient
import json

# MongoDB connection details
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["water_management"]  # Replace with your database name
collection = db["sensor_data"]  # Replace with your collection name

# MQTT broker details
mqtt_broker = "localhost"  # Replace with your MQTT broker address
mqtt_port = 1883  # Replace with your MQTT broker port if different

# Topic names
select_topic = "river/select"
result_topic = "river/result"

# Define the callback when a message is received
def on_message(client, userdata, message):
    query = json.loads(message.payload.decode("utf-8"))
    print(f"Received query: {query}")

    # Query MongoDB based on the received message
    result = collection.find(query)

    result_list = []
    for doc in result:
        # Convert ObjectId to string for easier handling
        doc["_id"] = str(doc["_id"])
        result_list.append(doc)

    if result_list:
        print(f"Found documents: {result_list}")
        # Publish the result back to another topic if needed
        client.publish(result_topic, json.dumps(result_list))
    else:
        print("No documents found")
        client.publish(result_topic, "No documents found")

# Set up the MQTT client
client = mqtt.Client()

# Set the on_message callback
client.on_message = on_message

# Connect to the MQTT broker
client.connect(mqtt_broker, mqtt_port)

# Subscribe to the topic
client.subscribe(select_topic)

# Start the MQTT client loop to listen for messages
client.loop_start()

# Keep the script running to listen for messages
print("MQTT client is running and waiting for messages...")
try:
    while True:
        pass  # Keep the script running
except KeyboardInterrupt:
    print("Disconnecting MQTT client...")
    client.loop_stop()
    client.disconnect()