from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from math import sin, cos, sqrt, radians, atan2
from pyproj import Proj, transform
import pyproj
from operator import itemgetter
import requests
from datetime import datetime
from sqlalchemy import create_engine, text
from os import environ
import json

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

carpark_URL = environ.get('carpark_URL') or "http://localhost:5001/consolidated"

db = SQLAlchemy(app)
class Location(db.Model):
    __tablename__ = 'location'

    carparkName = db.Column(db.String(100), primary_key=True)
    coordinates = db.Column(db.String(50))

    def __init__(self, carparkName, coordinates):
        self.carparkName = carparkName
        self.coordinates = coordinates

    def json(self):
        return {"carparkName": self.carparkName, "coordinates": self.coordinates}

@app.route("/data")
def get_data():
    # Retrieve location data from the external API
    # Retrieve location data from the external API using invoke_http
    response = requests.get(carpark_URL)
    if response.status_code != 200:
        # Handle the case where the request fails
        return jsonify({"error": "Failed to retrieve data from the external API"}), 500

    carpark_data = response.json()  # Access the list of car park data
    
    # Extracting coordinates directly
    # Retrieve specific columns from the Location table
    location_data = Location.query.with_entities(Location.coordinates).all()
    location_data = [row.coordinates for row in location_data]  # Extracting coordinates directly

    # Calculate the range 
    lon1 = radians(float(location_data[0].split(',')[0]))
    lat1 = radians(float(location_data[0].split(',')[1]))

    # Define the SVY21 and WGS84 CRS manually
    svy21_crs = pyproj.CRS.from_string('EPSG:3414')
    wgs84_crs = pyproj.CRS.from_string('EPSG:4326')
    # Create transformer
    transformer = pyproj.Transformer.from_crs(svy21_crs, wgs84_crs)

    # Filter car parks based on the current time
    filtered_carpark_data = []
    for ppCode, carpark in carpark_data.items():  # Iterate over each car park
        coordinates = (float(carpark["coordinates"].split(',')[0]), float(carpark["coordinates"].split(',')[1]))
        longitude2 = coordinates[0]
        latitude2 = coordinates[1]
        lon2, lat2 = transformer.transform(latitude2, longitude2)
        radlon2 = radians(lon2)
        radlat2 = radians(lat2)
        dlon = radlon2 - lon1 
        dlat = radlat2 - lat1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(radlat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = c * 6371.0

        # Append the relevant data along with distance
        carpark_info = {
            "ppCode": ppCode,  # Use ppCode as the key
            "coordinates": f"{lon2},{lat2}",
            "ppName": carpark["ppName"],
            "distance": distance,
            "parkingSystem": carpark["parkingSystem"]
        }
        filtered_carpark_data.append(carpark_info)
    
    # Sort car parks by distance and return the top 10 nearest ones
    top_10_nearest = sorted(filtered_carpark_data, key=lambda x: x['distance'])[:10]
    
    return top_10_nearest

with app.app_context():
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    with engine.connect() as connection:
        connection.execute(text("CREATE DATABASE IF NOT EXISTS location"))
    db.create_all()
    # Insert a new record if the Location table is empty
    if db.session.query(Location).count() == 0:  # Check if the table is empty
        new_location = Location('singapore management university', '1.2962727,103.8501578')  # Create a new location
        db.session.add(new_location)  # Add the new location to the session
        db.session.commit()  # Commit the session to save the changes
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4002, debug=True)


