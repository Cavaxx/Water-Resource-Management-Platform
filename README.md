# Water Resource Management Platform

This project aims to design a platform for managing the water resources and the facilities processing water bodies in the Trentino region. The system collect data from various sources, provinding the user with real time weather of its city, the monthly drought index and the the annual SPEI (s precipitation evotranspiration) index. It also provide a map with the water facilities and the dams present on the therritory with their realtime water level.

## Project Structure
- `data/`: Data storage
- `data fetcher/`: Script for fetching real time data
- `scripts/`: Data processing scripts
- `Spark_app/`: Spark models for computing the drought indexes
- `Interface/`: UI and Flask script

## Technologies Used
- Spark Streaming: Used for processing and analyzing the real-time data streams to compute the SPEI index and th.
- MongoDB: Used as the primary database to store the raw and processed weather data.
- Docker + Docker Compose: Used to containerize and orchestrate the deployment of all components and services.
- Flask (Python framework): Used to develop the User Interface, providing an interactive web application for users to input and view data.


