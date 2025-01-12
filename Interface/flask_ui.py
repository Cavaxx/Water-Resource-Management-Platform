from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # for headless (server) environments
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)

# MongoDB setup
mongo_client = MongoClient("mongodb://mongo:27017/")
db = mongo_client["water_management"]

# -----------------------------------------------------------
# Collections: 
# -----------------------------------------------------------
#   - 'SPEI_PET' has e.g. { city: "Trento", month: 1, pet: ..., spei: ... }
#   - 'water_facilities' has e.g. { nome: "TRENTO", ... }
spei_pet_collection = db["SPEI_PET"] # used in search results page
facilities_collection = db["water_facilities_trento"] # used in map page
river_collection = db["sensor_data"] # used in map page


# (Optional) If you still need a CSV for reference
csv_path = "/app/data/water_facilities_trentino.csv"
try:
    facilities_df = pd.read_csv(csv_path)
    facilities_df.set_index("id_sito", inplace=True)
except Exception as e:
    print(f"Error loading CSV data: {e}")

# Save City name list for search bar
def get_names_from_csv(file_path):
    df = pd.read_csv(file_path)
    return df['Denominazione in italiano'].tolist()

# Load city names from CSV file
city_csv_path = "../app/data/cod_com.csv"
city_list = get_names_from_csv(city_csv_path)



# -----------------------------------------------------------
# Routes to render templates
# -----------------------------------------------------------
@app.route('/')
def home():
    return render_template('Website.html')

@app.route('/contacts')
def contacts_page():
    return render_template('contacts.html')

@app.route('/services')
def services_page():
    # Render a template with your services info
    return render_template('services.html')

#---------------------------------
# Search Bar
#---------------------------------

@app.route('/search', methods=['GET'])
def search_city():
    city_name = request.args.get("city")  # e.g. /search?city=Trento
    if not city_name:
        return jsonify({"error": "No city name provided"}), 400
    
    if city_name not in city_list:
        return jsonify({'error': 'Invalid city name. Please enter a valid city.'}), 400

    # -- Query collections --
    spei_query = {"city": city_name}
    spei_pet_data = list(spei_pet_collection.find(spei_query, {"_id": 0}))

    fac_query = {"nome": city_name.upper()}
    facilities_data = list(facilities_collection.find(fac_query, {"_id": 0}))


    # Only take the first 12 records for charting (if that many exist)
    subset = spei_pet_data[:12]

    # Extract months, spei, and drought
    # If your docs store:  "month": int, "spei": float, "drought": float
    months = [rec.get("month") for rec in subset]
    spei_values = [rec.get("spei") for rec in subset]
    drought_values = [rec.get("drought") for rec in subset]

    # Optionally define a dictionary for month-name mapping
    month_map = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }
    month_labels = [month_map.get(m, f"Month {m}") for m in months]

    # ---------------------------------
    # (A) FIRST FIGURE: SPEI
    # ---------------------------------
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    ax1.plot(months, spei_values, marker='o', color='blue', label='SPEI')
    ax1.set_xlabel("Month")
    ax1.set_ylabel("SPEI Value")
    ax1.set_title(f"SPEI for {city_name}")
    ax1.set_xticks(months)
    ax1.set_xticklabels(month_labels, rotation=45)
    ax1.legend()
    fig1.tight_layout()

    # Convert to PNG bytes, then base64-encode
    png1 = BytesIO()
    fig1.savefig(png1, format="png")
    png1.seek(0)
    graph_data_spei = base64.b64encode(png1.getvalue()).decode('ascii')

    # ---------------------------------
    # (B) SECOND FIGURE: Drought
    # ---------------------------------
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.plot(months, drought_values, marker='o', color='red', label='Drought')
    ax2.set_xlabel("Month")
    ax2.set_ylabel("Drought Value")
    ax2.set_title(f"Drought for {city_name}")
    ax2.set_xticks(months)
    ax2.set_xticklabels(month_labels, rotation=45)
    ax2.legend()
    fig2.tight_layout()

    # Convert to PNG bytes, then base64-encode
    png2 = BytesIO()
    fig2.savefig(png2, format="png")
    png2.seek(0)
    graph_data_drought = base64.b64encode(png2.getvalue()).decode('ascii')

    # Clean up figures from memory
    plt.close(fig1)
    plt.close(fig2)

    # ---------------------------------
    # Render template, passing both images
    # ---------------------------------
    return render_template(
        "search_results.html",
        query=city_name,
        spei_pet_data=spei_pet_data,
        facilities_data=facilities_data,
        graph_data_spei=graph_data_spei,
        graph_data_drought=graph_data_drought
    )

# ---------------------------------
# MAP COORDINATES AND INFOS
# ---------------------------------
@app.route('/map')
def map_page():
    # Query the water facilities collection
    facilities = list(facilities_collection.find({}, {
        '_id': 0,
        'id_sito': 1,
        'longitude': 1,
        'latitude': 1,
        'comuni_serviti': 1,
        'descrizione': 1
    }))
    
    # Query the river collection
    rivers = list(river_collection.find({}, {
        '_id': 0,
        'timestamp': 1,
        'site': 1,
        'value': 1,
        'longitude': 1,
        'latitude': 1
    }))

    return render_template('map.html', 
                           facilities=facilities,
                           rivers=rivers)



if __name__ == '__main__':
    # Debug mode for local development; 0.0.0.0 to listen on all interfaces in Docker
    app.run(debug=True, host='0.0.0.0', port=5001)
