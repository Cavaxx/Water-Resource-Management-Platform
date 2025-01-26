# Use a Python 3.10 base image
FROM python:3.10

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libatlas-base-dev \
    libffi-dev \
    libssl-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements.txt first (to leverage Docker's caching)
COPY requirements.txt /app/

# Upgrade pip and setuptools
RUN pip install --upgrade pip setuptools

# Install Python packages from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Verify we have correct versions installed (optional checks)
RUN python -c "import sys; print('Python version:', sys.version)"
RUN python -c "import numpy; print('NumPy version:', numpy.__version__)"
RUN python -c "import pandas; print('Pandas version:', pandas.__version__)"

# Copy the rest of the application code into the container
COPY . /app/

# (Optional) Expose a port if your container offers a web endpoint 
# or if you plan to run a local MQTT broker here (generally not recommended).
# EXPOSE 1883

# Environment variables (override in docker-compose.yml if needed)
ENV MQTT_BROKER=localhost
ENV MQTT_PORT=1883
ENV WEATHER_API_KEY=YOUR_OPENWEATHERMAP_API_KEY

# By default, run the weather-data fetch script
CMD ["python", "fetch_weather_data.py"]
