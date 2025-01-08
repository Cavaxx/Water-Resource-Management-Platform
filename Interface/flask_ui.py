from os import sendfile
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import pandas as pd

app = Flask(__name__)

# MongoDB setup
mongo_client = MongoClient("mongodb://mongo:27017/")
db = mongo_client["water_management"]
rivers_collection = db["sensor_data"]

# Load CSV data
csv_path = "../data/water_facilities_trentino.csv"

@app.route('/get-csv-data')
def get_csv_data():
    # Read the CSV file
    data = []
    try:
        with open(csv_path, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
    except FileNotFoundError:
        return jsonify({"error": "CSV file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    return jsonify(data)

# Routes to render templates
@app.route('/')
def home():
    return render_template('Website.html')

@app.route('/map')
def map_page():
    return render_template('map.html')

@app.route('/contacts')
def contacts_page():
    return render_template('contacts.html')

@app.route('/services')
def services_page():
    return render_template('services.html')

# Search route
@app.route('/search', methods=['GET'])
def search_river():
    river_name = request.args.get('name')
    if river_name:
        river_query = {"water_body": river_name}
        river_results = list(rivers_collection.find(river_query, {"_id": 0, "water_body": 1, "value": 1, "latitude": 1, "longitude": 1}))
        facility_results = facilities_df[facilities_df['recettore'] == river_name].to_dict(orient="records")
        return jsonify({"river_data": river_results, "facility_data": facility_results})
    else:
        return jsonify({"error": "No river name provided"}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
