# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any necessary dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Flask port
EXPOSE 5001

# Define the environment variable for Flask
ENV FLASK_APP=flask_ui.py

# Run the command to start Flask
CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]
