FROM python:3.9-slim

# Create a working directory
WORKDIR /app

# Copy only the necessary files
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy your script into the container
COPY mqtt_ingestion.py /app/

# Set environment variables as needed
ENV MONGO_URI="mongodb://mongo:27017/" \
    MQTT_BROKER="mqtt-broker" \
    MQTT_PORT=1883 \
    TOPICS="city/water_facilities,sensors_data/river,weather_data/city,SPET_PET/city"

# Run the service
CMD ["python", "mqtt_ingestion.py"]
