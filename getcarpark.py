

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from math import sin, cos, sqrt, radians, atan2
from pyproj import Proj,transform 
import pyproj
from operator import itemgetter
import requests

app = Flask(__name__)
CORS(app)

# Configure SQLAlchemy for the first database (location)
app.config['SQLALCHEMY_BINDS'] = {
    'location': 'mysql+mysqlconnector://root:root@localhost:3306/location',
    'carpark': 'mysql+mysqlconnector://root:root@localhost:3306/carpark'
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Location(db.Model):
    __bind_key__ = 'location'
    __tablename__ = 'location'

    carparkName = db.Column(db.String(100), primary_key=True)
    coordinates = db.Column(db.String(50))

    def __init__(self, carparkName, coordinates):
        self.carparkName = carparkName
        self.coordinates = coordinates

    def json(self):
        return {"carparkName": self.carparkName, "coordinates": self.coordinates}


class Prices(db.Model):
    __bind_key__ = 'carpark'
    __tablename__ = 'prices'
    ppCode = db.Column(db.String(5), primary_key=True)
    weekdayMin = db.Column(db.String(10))
    weekdayRate = db.Column(db.String(10))
    parkingSystem = db.Column(db.String(1))
    ppName = db.Column(db.String(50))
    vehCat = db.Column(db.String(20))
    satdayMin = db.Column(db.String(10))
    satdayRate = db.Column(db.String(10))
    sunPHMin = db.Column(db.String(10))
    sunPHRate = db.Column(db.String(10))
    coordinates = db.Column(db.String(50))
    startTime = db.Column(db.String(10))
    parkCapacity = db.Column(db.Integer)
    endTime = db.Column(db.String(10))

    def __init__(self, ppCode, weekdayMin, weekdayRate, parkingSystem, ppName, vehCat, satdayMin, satdayRate, sunPHMin, sunPHRate, geometries, startTime, parkCapacity, endTime):
        self.ppCode = ppCode
        self.weekdayMin = weekdayMin
        self.weekdayRate = weekdayRate
        self.parkingSystem = parkingSystem
        self.ppName = ppName
        self.vehCat = vehCat
        self.satdayMin = satdayMin
        self.satdayRate = satdayRate
        self.sunPHMin = sunPHMin
        self.sunPHRate = sunPHRate
        self.coordinates = geometries[0].get('coordinates', '0,0') if geometries else '0,0'
        self.startTime = startTime
        self.parkCapacity = parkCapacity
        self.endTime = endTime

    def json(self):
        return {
            "ppCode": self.ppCode,
            "weekdayMin": self.weekdayMin,
            "weekdayRate": self.weekdayRate,
            "parkingSystem": self.parkingSystem,
            "ppName": self.ppName,
            "vehCat": self.vehCat,
            "satdayMin": self.satdayMin,
            "satdayRate": self.satdayRate,
            "sunPHMin": self.sunPHMin,
            "sunPHRate": self.sunPHRate,
            "coordinates": self.coordinates,
            "startTime": self.startTime,
            "parkCapacity": self.parkCapacity,
            "endTime": self.endTime
        }
    





@app.route("/data")

def get_data():
    # Retrieve location data from the external API
    response = requests.get("http://localhost:5001/getAllCarparks")
    if response.status_code != 200:
        # Handle the case where the request fails
        return jsonify({"error": "Failed to retrieve data from the external API"}), 500

    carpark_data = response.json()["data"]  # Access the list of car park data
    
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

    filtered_carpark_data = []
    for carpark in carpark_data:
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
        filtered_carpark_data.append({
            "coordinates": carpark["coordinates"],
            "endTime": carpark["endTime"],
            "lotType": carpark.get("lotType"),  # Assuming lotType might not be available for all car parks
            "lotsAvailable": carpark.get("lotsAvailable"),  # Assuming lotsAvailable might not be available for all car parks
            "parkCapacity": carpark["parkCapacity"],
            "parkingSystem": carpark["parkingSystem"],
            "ppCode": carpark["ppCode"],
            "ppName": carpark["ppName"],
            "satdayMin": carpark["satdayMin"],
            "satdayRate": carpark["satdayRate"],
            "startTime": carpark["startTime"],
            "sunPHMin": carpark["sunPHMin"],
            "sunPHRate": carpark["sunPHRate"],
            "vehCat": carpark["vehCat"],
            "weekdayMin": carpark["weekdayMin"],
            "weekdayRate": carpark["weekdayRate"],
            "distance": distance
        })

    # Sort the data based on distance
    filtered_carpark_data.sort(key=itemgetter('distance'))

    # Get the top 10 shortest distances
    top_10_distances = filtered_carpark_data[:10]

    return jsonify(top_10_distances)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4002, debug=True)


