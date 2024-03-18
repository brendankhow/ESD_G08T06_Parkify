

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from math import sin, cos, sqrt, radians, atan2
from pyproj import Proj,transform 
import pyproj
from operator import itemgetter

app = Flask(__name__)
CORS(app)

# Configure SQLAlchemy for the first database (location)
app.config['SQLALCHEMY_BINDS'] = {
    'location': 'mysql+mysqlconnector://root:root@localhost:8889/location',
    'carpark': 'mysql+mysqlconnector://root:root@localhost:8889/carpark'
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

    filtered_prices_data = []
    for row in Prices.query.all():
        longitude2 = float(row.coordinates.split(',')[0])
        latitude2 = float(row.coordinates.split(',')[1])
        lon2, lat2 = transformer.transform(latitude2, longitude2)
        radlon2 = radians(lon2)
        radlat2 = radians(lat2)
        dlon = radlon2 - lon1 
        dlat = radlat2 - lat1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(radlat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = c * 6371.0
        filtered_prices_data.append({
            "ppCode": row.ppCode,
            "weekdayMin": row.weekdayMin,
            "weekdayRate": row.weekdayRate,
            "parkingSystem": row.parkingSystem,
            "ppName": row.ppName,
            "vehCat": row.vehCat,
            "satdayMin": row.satdayMin,
            "satdayRate": row.satdayRate,
            "sunPHMin": row.sunPHMin,
            "sunPHRate": row.sunPHRate,
            "coordinates": row.coordinates,
            "startTime": row.startTime,
            "parkCapacity": row.parkCapacity,
            "endTime": row.endTime,
            "distance": distance
        })

    # Sort the data based on distance
    filtered_prices_data.sort(key=itemgetter('distance'))

    # Get the top 10 shortest distances
    top_10_distances = filtered_prices_data[:10]

    return jsonify(top_10_distances)




    
    



def reverse_coordinates(coordinates):
    lat, lng = coordinates.split(',')
    return f"{lng},{lat}"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4002, debug=True)


