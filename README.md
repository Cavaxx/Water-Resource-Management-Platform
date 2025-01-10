# Water Resource Management Platform

This project aims to design a comprehensive platform for managing water resources and the facilities processing water bodies in the Trentino region. The system collects data from various sources, providing users with real-time weather updates for their city, the monthly drought index, and the annual SPEI (Standardized Precipitation-Evapotranspiration Index). It also features a map showcasing water facilities and dams within the region, along with their real-time water levels.
Project Structure
- data/: Data storage
- data fetcher/: Scripts for fetching real-time data
- scripts/: Data processing scripts
- Spark_app/: Apache Spark models for computing drought indexes
- Interface/: User Interface and Flask server

## Technologies Used

- Apache Spark: Used for distributed processing of real-time data streams to calculate the SPEI index and perform drought analysis​
- MongoDB: Acts as the primary NoSQL database to store raw and processed weather data​
- Docker & Docker Compose: Facilitates containerization and orchestration of services, ensuring consistent deployment across environments​
- Flask (Python Framework): Powers the web-based User Interface for interactive data visualization​
- PySpark: Provides a Python interface for Apache Spark, enabling large-scale data analysis​
- Climate-Indices Library: Computes drought indices using methods like Thornthwaite PET and SPEI calculations​
- Matplotlib & Pandas: Used for data analysis and visualization within the Flask app​
- Python Scheduling & Requests Libraries: Automates regular data fetching and processing tasks​


