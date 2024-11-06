from pyspark.sql import SparkSession
from flask import Flask, request, jsonify

app = Flask(__name__)



# Initialize Spark session with MongoDB connector
spark = SparkSession.builder \
    .appName("WaterFlowSearch") \
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.4.0") \
    .config("spark.mongodb.read.connection.uri", "mongodb://127.0.0.1/water_management.sensor_data") \
    .getOrCreate()

# Load MongoDB data for river water flow by specifying collection at load time
try:
    rivers_df = spark.read \
        .format("mongodb") \
        .option("database", "water_management") \
        .option("collection", "sensor_data") \
        .load()
    rivers_df.show(5)  # Display the first 5 records to verify loading
except Exception as e:
    print("Error loading data from MongoDB:", e)


# Load CSV data for water facilities
try:
    facilities_df = spark.read.csv("/home/ubuntu/Data_Science/Water-Resource-Management-Platform/data/water_facilities_trentino.csv", header=True, inferSchema=True)
    facilities_df.createOrReplaceTempView("facilities")
    facilities_df.show(5)  # Show the first few rows to verify
except Exception as e:
    print("Error loading CSV data:", e)

# Flask route to handle search
@app.route('/search', methods=['GET'])
def search_river():
    river_name = request.args.get('name')
    if river_name:
        # Construct queries for MongoDB river data and facility CSV data
        river_query = f"SELECT water_body AS Name_River, value AS Water_Level, latitude, longitude FROM rivers WHERE water_body = '{river_name}'"
        facility_query = f"SELECT * FROM facilities WHERE recettore = '{river_name}'"
        
        # Execute queries
        river_results = spark.sql(river_query).collect()
        facility_results = spark.sql(facility_query).collect()

        # Convert results to JSON format for response
        river_json = [
            {"Name_River": row.Name_River, "Water_Level": row.Water_Level, "latitude": row.latitude, "longitude": row.longitude}
            for row in river_results
        ]
        facility_json = [
            {
                "Facility_Name": row.descrizione,
                "ID_Site": row.id_sito,
                "Description": row.comuni_serviti,
                "latitude": row.latitude, 
                "longitude": row.longitude
            }
            for row in facility_results if row.latitude and row.longitude
        ]
        
        return jsonify({"river_data": river_json, "facility_data": facility_json})
    else:
        return jsonify({"error": "No river name provided"}), 400

if __name__ == '__main__':
    # Run the Flask app on an alternative port (5001) to avoid conflicts
    app.run(debug=True, port=5001)
