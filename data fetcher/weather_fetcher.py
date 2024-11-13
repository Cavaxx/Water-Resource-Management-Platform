import paho.mqtt.client as mqtt
import requests
import json
from pymongo import MongoClient
import yaml

mongo_client = MongoClient('mongodb://mongo:27017/')
db = mongo_client['data_db']
collection = db['data_row']

mqtt_broker = 'mosquitto'
mqtt_topic_city = 'city/select'
mqtt_topic_data_raw = 'city/data_raw'

client = mqtt.Client()

def fetch_current_weather(api_key, city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Failed to fetch current weather data for {city}. Response: {response.text}")
        return None

def fetch_forecast(api_key, city):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Failed to fetch forecast data for {city}. Response: {response.text}")
        return None

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(mqtt_topic_city)
    print(f"Subscribed to topic: {mqtt_topic_city}")

def on_message(client, userdata, msg):
    try:
        city = msg.payload.decode()
        print(f"Received city: {city}")
        if not city:
            print("Error: Received empty city name")
            return

        with open("config.yaml", "r") as f:
            config_data = yaml.safe_load(f)
        api_key = config_data["API"]["api"]

        current_weather = fetch_current_weather(api_key, city)
        forecast_data = fetch_forecast(api_key, city)

        if current_weather and forecast_data:
            raw_data = {
                'city': city,
                'current_weather': current_weather,
                'forecast_data': forecast_data
            }

            result = collection.insert_one(raw_data)
            print(f"Inserted raw data for {city} into MongoDB with ID: {result.inserted_id}")

            raw_data.pop('_id', None)

            print(f"Publishing raw data to MQTT topic {mqtt_topic_data_raw}: {json.dumps(raw_data)}")
            client.publish(mqtt_topic_data_raw, json.dumps(raw_data))
            print(f"Published raw data for {city} to MQTT")
        else:
            print(f"Failed to fetch data for {city}")

    except Exception as e:
        print(f"Error processing message for city {city}: {e}")


client.on_connect = on_connect
client.on_message = on_message

print("Connecting to MQTT broker...")
try:
    client.connect(mqtt_broker, 1883, 60)
    print("Connected to MQTT broker")
except Exception as e:
    print(f"Failed to connect to MQTT broker: {e}")

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("Disconnecting from MQTT broker")
    client.disconnect()
    print("Disconnected from MQTT broker")