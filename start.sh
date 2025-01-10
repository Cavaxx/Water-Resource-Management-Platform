#!/bin/bash

# Desired daily schedule (24-hour format)
TARGET_HOUR="02"
TARGET_MINUTE="00"

# Path to your docker-compose file (if not in the current directory)
DOCKER_COMPOSE_FILE="docker-compose.yml"

# Function to check if it's time to run the job
check_time_and_run() {
    current_hour=$(date +%H)
    current_minute=$(date +%M)

    if [[ "$current_hour" == "$TARGET_HOUR" && "$current_minute" == "$TARGET_MINUTE" ]]; then
        echo "[$(date)] Starting Spark application..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" up --build --abort-on-container-exit
        echo "[$(date)] Spark application run completed."
        # Sleep for one minute to avoid restarting within the same minute
        sleep 60
    else
        # Sleep for a short duration before checking again
        sleep 30
    fi
}

# Infinite loop to continuously check the time
while true; do
    check_time_and_run
done
