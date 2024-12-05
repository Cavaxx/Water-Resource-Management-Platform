import requests
import os
from pymongo import MongoClient

# URL to fetch the JSON data
url = "https://telecontrollo.cliquenet.it/opendata/siti"

# Keys to extract from the JSON
keys = ["id_sito", "indirizzo", "comune", "comuni_serviti", "descrizione", "longitude", "latitude", "altezza_mslm", "nome", "recettore"]

# Define MongoDB URI, defaulting to localhost if not provided as an environment variable
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

# Connect to MongoDB client
client = MongoClient(MONGO_URI)

# Access the 'water_management' database and 'water_facilities_trento' collection
db = client["water_management"]
collection_name = "water_facilities_trento"
collection = db[collection_name]

# Function to create MongoDB collection if it doesn't already exist
def create_collection(db, collection_name):
    if collection_name not in db.list_collection_names():
        db.create_collection(collection_name)
        print(f"Collection '{collection_name}' created successfully in database 'water_management'.")
    else:
        print(f"Collection '{collection_name}' already exists in database 'water_management'.")

# Function to fetch JSON data from the URL
def fetch_json_data(url):
    response = requests.get(url)
    response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
    return response.json()

# Function to insert JSON data into MongoDB collection
def insert_data_into_mongodb(json_data, collection, keys):
    documents = []
    for item in json_data:
        document = {key: item.get(key, "") for key in keys}
        documents.append(document)
    # Insert documents into MongoDB collection
    collection.insert_many(documents)
    print(f"{len(documents)} records inserted into '{collection_name}' collection.")

# Main function
def main():
    # Fetch JSON data
    json_data = fetch_json_data(url)
    
    # Create MongoDB collection if it doesn't exist
    create_collection(db, collection_name)
    
    # Insert data into MongoDB collection
    insert_data_into_mongodb(json_data, collection, keys)

# Run the main function if the script is executed directly
if __name__ == "__main__":
    main()
