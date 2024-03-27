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

app = Flask(__name__)
CORS(app)

# Configure SQLAlchemy for the first database (location)
app.config['SQLALCHEMY_BINDS'] = {
    'location': 'mysql+mysqlconnector://root:root@localhost:3306/location',
    'carpark': 'mysql+mysqlconnector://root:root@localhost:3306/carpark'
}
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:3306/location'
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

# Convert SVY21 coordinates to WGS84 format
def convert_coordinates_to_wgs84(coordinates):
    svy21_crs = pyproj.CRS.from_string('EPSG:3414')
    wgs84_crs = pyproj.CRS.from_string('EPSG:4326')
    transformer = pyproj.Transformer.from_crs(svy21_crs, wgs84_crs)
    lon, lat = transformer.transform(coordinates[1], coordinates[0])  # Transform (x, y) to (lon, lat)
    return lon, lat

@app.route("/data")
def get_data():
    # Retrieve location data from the external API
    response = requests.get("http://localhost:5001/consolidated")
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

    # Get the current time
    current_time = datetime.now().strftime('%I:%M %p')
    
    # Filter car parks based on the current time
    filtered_carpark_data = []
    for ppCode, carpark in carpark_data.items():  # Iterate over each car park
        # Check if "Car" exists in the "vehicles" dictionary
        if "Car" in carpark.get("vehicles", {}):
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
            
            # Convert start times to comparable format and check if current time falls within the range
            start_times = [datetime.strptime(time, "%I.%M %p") for time in carpark["vehicles"]["Car"]["pricing"]["startTime"]]
            for i, start_time in enumerate(start_times):
                # Adjust for times spanning midnight
                if i > 0 and start_times[i] < start_times[i-1]:
                    start_times[i] = start_times[i].replace(day=start_times[i].day + 1)
            if any(start_time <= datetime.strptime(current_time, "%I:%M %p") <= end_time for start_time, end_time in zip(start_times, start_times[1:] + [start_times[0]])):
                # Append the relevant data along with distance
                carpark_info = {
                    "ppCode": ppCode,  # Use ppCode as the key
                    "coordinates": f"{lon2},{lat2}",
                    "endTime": carpark["vehicles"]["Car"]["pricing"]["endTime"][i],  # Assumes matching index
                    "lotType": carpark.get("lotType"),
                    "lotsAvailable": carpark.get("lotsAvailable"),
                    "parkCapacity": carpark["vehicles"]["Car"]["parkCapacity"],
                    "parkingSystem": carpark["parkingSystem"],
                    "ppName": carpark["ppName"],
                    "satdayMin": carpark["vehicles"]["Car"]["pricing"]["satdayMin"][i],  # Assumes matching index
                    "satdayRate": carpark["vehicles"]["Car"]["pricing"]["satdayRate"][i],  # Assumes matching index
                    "startTime": carpark["vehicles"]["Car"]["pricing"]["startTime"][i],  # Assumes matching index
                    "sunPHMin": carpark["vehicles"]["Car"]["pricing"]["sunPHMin"][i],  # Assumes matching index
                    "sunPHRate": carpark["vehicles"]["Car"]["pricing"]["sunPHRate"][i],  # Assumes matching index
                    "weekdayMin": carpark["vehicles"]["Car"]["pricing"]["weekdayMin"][i],  # Assumes matching index
                    "weekdayRate": carpark["vehicles"]["Car"]["pricing"]["weekdayRate"][i],  # Assumes matching index
                    "distance": distance
                }
                filtered_carpark_data.append(carpark_info)
    
    # Sort car parks by distance and return the top 10 nearest ones
    top_10_nearest = sorted(filtered_carpark_data, key=lambda x: x['distance'])[:10]
    
    return top_10_nearest


with app.app_context():
    engine = create_engine('mysql+mysqlconnector://root:root@localhost:3306')
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


