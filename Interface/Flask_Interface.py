from flask import Flask, render_template, request, jsonify
import json
import paho.mqtt.client as mqtt
import time

app = Flask(__name__)

# MQTT setup
mqtt_broker = 'mosquitto'
mqtt_topic_city = 'city/select'
mqtt_topic_data_filtered = 'city/data_filtered'
mqtt_topic_alerts = 'city/synthetic_data' 