# Use the full Python image
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

# Copy requirements.txt first to leverage Docker cache
COPY requirements.txt /app/

# Upgrade pip and setuptools
RUN pip install --upgrade pip setuptools

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Print versions to verify
RUN python -c "import sys; print('Python version:', sys.version)"
RUN python -c "import numpy; print('NumPy version:', numpy.__version__)"
RUN python -c "import pandas; print('Pandas version:', pandas.__version__)"

# Copy the rest of the application code
COPY . /app/

# Expose port if necessary (optional)
EXPOSE 80

# Run the application
CMD ["python", "fetch_weather_data.py"]
