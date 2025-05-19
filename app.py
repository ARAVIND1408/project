from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests
import logging
from functools import wraps
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Airtable Configuration
AIRTABLE_BASE_ID = 'appqd5RgY61IFtaCW'
AIRTABLE_TABLE_NAME = 'Monitor'
AIRTABLE_PAT = 'patiwo0rfyrmWW12O.5225c432ca3efa87616f44ef82c655e36676ff4cbe1d9b722951ee95a10f2f82'

def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return jsonify({'error': 'Failed to connect to Airtable', 'details': str(e)}), 500
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500
    return wrapper

def fetch_single_house_data(house_id):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT}"
    }
    params = {
        "filterByFormula": f"HouseID = '{house_id}'"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        records = response.json().get('records', [])
        if not records:
            return None
        
        record = records[0]
        fields = record.get('fields', {})
        
        try:
            water_used = float(fields.get('WaterUsed', 0))
            price = float(fields.get('Price', 0))
        except (ValueError, TypeError):
            water_used = 0
            price = 0
            logger.warning(f"Invalid numeric values for HouseID {house_id}")
        
        return {
            'HouseID': str(fields.get('HouseID', 'Unknown')),
            'WaterUsed': water_used,
            'Price': price
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Airtable API request failed: {str(e)}")
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/water-consumption/<house_id>')
@handle_errors
def api_single_house(house_id):
    data = fetch_single_house_data(house_id)
    if not data:
        return jsonify({'error': 'House not found', 'details': f'No data for HouseID {house_id}'}), 404
    return jsonify(data)

if __name__ == '__main__':
    port = int(os.environ.get("PORT",5000))
    app.run(host='0.0.0.0', port=port, debug=True)
