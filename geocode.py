from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import pyproj
import googlemaps
import time
from os import environ

app = Flask(__name__)
CORS(app)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:8889/location'
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the coordinate systems
wgs84 = pyproj.CRS('EPSG:4326')  # WGS84 coordinate system (Google Maps)
svy21 = pyproj.CRS('EPSG:3414')  # SVY21 coordinate system

# Create a transformer to convert between coordinate systems
transformer = pyproj.Transformer.from_crs(wgs84, svy21)

class Location(db.Model):
    __tablename__ = 'location'

    carparkName = db.Column(db.String(100), primary_key=True)
    coordinates = db.Column(db.String(50))

    def __init__(self, carparkName, coordinates):
        self.carparkName = carparkName
        self.coordinates = coordinates

    def json(self):
        return {"carparkName": self.carparkName, "coordinates": self.coordinates}


def fetch_carpark_coordinates(location):
    # Clear previous search results
    db.session.query(Location).delete()
    db.session.commit()

    API_KEY = 'AIzaSyBx3sJpEQFY3o-4VYkT7Zfcwh8OABpTS-s'
    map_client = googlemaps.Client(API_KEY)

    # Retrieve geocoding information for the provided location
    geocode_result = map_client.geocode(address=location)

    if geocode_result:
        # Extract latitude and longitude from the geocoding result
        latitude = geocode_result[0]['geometry']['location']['lat']
        longitude = geocode_result[0]['geometry']['location']['lng']
        
        # Convert the latitude and longitude to a string format
        coordinates = f"{latitude},{longitude}"
        
        # Check if car park exists, update if it does, otherwise insert new
        carpark = Location.query.get(location)
        if carpark:
            carpark.coordinates = coordinates
        else:
            new_carpark = Location(carparkName=location, coordinates=coordinates)
            db.session.add(new_carpark)
        db.session.commit()
        return jsonify({"message": "Carpark location updated successfully."}), 200
    else:
        return jsonify({"message": "No location found for the provided input."}), 404

@app.route("/locations/update")
def update_carpark_locations():
    fetch_carpark_coordinates()
    return jsonify({"message": "Carpark locations updated successfully."}), 200

@app.route("/location")
def get_carpark_location():
    locations = Location.query.all()
    if locations:
        return jsonify({"locations": [location.json() for location in locations]})
    else:
        return jsonify({"message": "No carpark locations found."}), 404

@app.route("/locations", methods=['GET'])
def get_carpark_locations():
    # Get the search query from the frontend
    location = request.args.get('location')
    
    # Fetch carpark locations based on the search query
    fetch_carpark_coordinates(location)
    
    # Retrieve and return the locations from the database
    locations = Location.query.all()
    if locations:
        return jsonify({"locations": [location.json() for location in locations]})
    else:
        return jsonify({"message": "No carpark locations found."}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001, debug=True)
