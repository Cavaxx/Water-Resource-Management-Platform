from flask import Flask, request, jsonify, render_template
import pandas as pd


app = Flask(__name__)

# Load CSV data
def get_names_from_csv(file_path):
    df = pd.read_csv(file_path)
    return df['Denominazione in italiano'].tolist()

# Load city names from CSV file
city_csv_path = "../app/data/cod_com.csv"
city_names = get_names_from_csv(city_csv_path)

# Replace with your Weather API key
API_KEY = 'your_api_key'
BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'

@app.route('/')
def home():
    return render_template('Website.html'), 200, {'Content-Type': 'text/html'}

@app.route('/get-weather', methods=['POST'])
def get_weather():
    city = request.form['city']
    if not city:
        return jsonify({'error': 'City name is required'}), 400

    # Validate city against CSV list
    if city not in city_names:
        return jsonify({'error': 'Invalid city name. Please enter a valid city.'}), 400

    # Make API request
    params = {'q': city, 'appid': API_KEY, 'units': 'metric'}
    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        weather = {
            'city': data['name'],
            'temperature': data['main']['temp'],
            'description': data['weather'][0]['description'],
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed']
        }
        return render_template('result.html', weather=weather)
    else:
        return jsonify({'error': 'City not found or API error'}), 404

# Load CSV data
csv_path = "../app/data/water_facilities_trentino.csv"
try:
    facilities_df = pd.read_csv(csv_path)
    facilities_df.set_index("id_sito", inplace=True)
except Exception as e:
    print(f"Error loading CSV data: {e}")

@app.route('/csv_data')
def get_csv_data():
    return send_file(csv_path, as_attachment=False)

@app.route('/map')
def map_page():
    return render_template('map.html')

@app.route('/contacts')
def contacts_page():
    return render_template('contacts.html')

@app.route('/services')
def services_page():
    return render_template('services.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
