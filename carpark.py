from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import environ
import requests
import logging

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:8889/carpark'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Lots(db.Model): 
    __tablename__ = 'lotsAvailability'
    carparkNo = db.Column(db.String(5), primary_key=True)
    coordinates = db.Column(db.String(50))  # Changed to String to match your data format
    lotsAvailable = db.Column(db.Integer, nullable=False)
    lotType = db.Column(db.String(1), nullable=False)

    def __init__(self, carparkNo, geometries, lotsAvailable, lotType):
        self.carparkNo = carparkNo
        # self.coordinates = geometries[0]['coordinates'] if geometries else None  # Assuming the first geometry is what you want
        self.coordinates = geometries[0].get('coordinates', '0,0') if geometries else '0,0'
        self.lotsAvailable = lotsAvailable
        self.lotType = lotType

    def json(self):
        return {"carparkNo": self.carparkNo, "coordinates": self.coordinates, "lotsAvailable": self.lotsAvailable, "lotType": self.lotType}

class Prices(db.Model):
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

class Season(db.Model):
    __tablename__ = 'season'
    ppCode = db.Column(db.String(5), primary_key=True)
    ppName = db.Column(db.String(50))
    vehCat = db.Column(db.String(20))
    monthlyRate = db.Column(db.String(20))
    coordinates = db.Column(db.String(50))
    parkingHrs = db.Column(db.String(50))
    ticketType = db.Column(db.String(20))

    def __init__(self, ppCode, ppName, vehCat, monthlyRate, geometries, parkingHrs, ticketType):
        self.ppCode = ppCode
        self.ppName = ppName
        self.vehCat = vehCat
        self.monthlyRate = monthlyRate
        self.coordinates = geometries[0].get('coordinates', '0,0') if geometries else '0,0'
        self.parkingHrs = parkingHrs
        self.ticketType = ticketType

    def json(self):
        return {
            "ppCode": self.ppCode,
            "ppName": self.ppName,
            "vehCat": self.vehCat,
            "monthlyRate": self.monthlyRate,
            "coordinates": self.coordinates,
            "parkingHrs": self.parkingHrs,
            "ticketType": self.ticketType,
        }
    
def get_daily_token(access_key):
    url = "https://www.ura.gov.sg/uraDataService/insertNewToken.action"
    headers = {
        "AccessKey": access_key,
        "User-Agent": "MyApp/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        token_data = response.json()
        if token_data.get("Status") == "Success":
            return token_data.get("Result")
        else:
            logging.error(f"Failed to get token, response: {token_data}")
    else:
        logging.error(f"Failed to get token, status code: {response.status_code}, response: {response.text}")
    return None

def fetch_carpark_lotsAvailability():
    access_key = "8279da0e-f5f2-45e3-8329-f62d4b0e9a47"  # Replace with your actual access key
    token = get_daily_token(access_key)
    if not token:
        logging.error("Failed to fetch carpark lots data due to token retrieval failure.")
        return []

    url = "https://www.ura.gov.sg/uraDataService/invokeUraDS?service=Car_Park_Availability"
    headers = {
        "AccessKey": access_key,
        "Token": token,
        "User-Agent": "MyApp/1.0",
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200 and response.headers.get('Content-Type') == 'application/json':
        return response.json().get("Result", [])
    else:
        logging.error(f"Failed to fetch carpark lots data, status code: {response.status_code}, response: {response.text}")
        return []
    
def insert_carpark_lotsAvailability(lots_data):
    for item in lots_data:
        carparkNo = item.get("carparkNo")
        lotType = item.get("lotType")
        lotsAvailable = int(item.get("lotsAvailable"))
        geometries = item.get("geometries", [{}])  # Keep as list of dictionaries

        # Check if carpark already exists to update or insert new
        lotsAvailability = Lots.query.filter_by(carparkNo=carparkNo).first()
        if lotsAvailability:
            lotsAvailability.coordinates = geometries[0].get("coordinates", "0,0") if geometries else "0,0"
            lotsAvailability.lotsAvailable = lotsAvailable
            lotsAvailability.lotType = lotType
            # Assuming the first geometry's coordinates is what you want
  
        else:
            # Correctly pass geometries to the constructor
            lotsAvailability = Lots(carparkNo=carparkNo, geometries=geometries, lotsAvailable=lotsAvailable, lotType=lotType)
            db.session.add(lotsAvailability)
    
    try:
        db.session.commit()
    except Exception as e:
        logging.error(f"An error occurred while inserting/updating the carpark lots data: {e}")
        db.session.rollback()

def fetch_carpark_prices():
    access_key = "8279da0e-f5f2-45e3-8329-f62d4b0e9a47"  # Replace with your actual access key
    token = get_daily_token(access_key)
    if not token:
        logging.error("Failed to fetch carpark prices data due to token retrieval failure.")
        return []
    
    url = "https://www.ura.gov.sg/uraDataService/invokeUraDS?service=Car_Park_Details"
    headers = {
        "AccessKey": access_key,
        "Token": token,
        "User-Agent": "MyApp/1.0",
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200 and response.headers.get('Content-Type') == 'application/json':
        return response.json().get("Result", [])
    else:
        logging.error(f"Failed to fetch carpark prices data, status code: {response.status_code}, response: {response.text}")
        return []
    
def insert_carpark_prices(prices_data):
    for item in prices_data:
        ppCode = item.get("ppCode")
        price = Prices.query.filter_by(ppCode=ppCode).first()
        # Safely handle geometries list to avoid IndexError
        geometries = item.get("geometries", [{}])  # Keep as list of dictionaries
        coordinates = geometries[0].get("coordinates", "0,0") if geometries else "0,0"

        if price:
            # Update existing record
            price.weekdayMin = item.get("weekdayMin")
            price.weekdayRate = item.get("weekdayRate")
            price.parkingSystem = item.get("parkingSystem")
            price.ppName = item.get("ppName")
            price.vehCat = item.get("vehCat")
            price.satdayMin = item.get("satdayMin")
            price.satdayRate = item.get("satdayRate")
            price.sunPHMin = item.get("sunPHMin")
            price.sunPHRate = item.get("sunPHRate")
            price.coordinates = geometries[0].get("coordinates", "0,0") if geometries else "0,0"
            price.startTime = item.get("startTime")
            price.parkCapacity = item.get("parkCapacity")
            price.endTime = item.get("endTime")
        else:
            # Insert new record
            new_price = Prices(
                ppCode=ppCode,
                weekdayMin=item.get("weekdayMin"),
                weekdayRate=item.get("weekdayRate"),
                parkingSystem=item.get("parkingSystem"),
                ppName=item.get("ppName"),
                vehCat=item.get("vehCat"),
                satdayMin=item.get("satdayMin"),
                satdayRate=item.get("satdayRate"),
                sunPHMin=item.get("sunPHMin"),
                sunPHRate=item.get("sunPHRate"),
                geometries=geometries,
                startTime=item.get("startTime"),
                parkCapacity=item.get("parkCapacity"),
                endTime=item.get("endTime")
            )
            db.session.add(new_price)
    db.session.commit()

def fetch_carpark_season():
    access_key = "8279da0e-f5f2-45e3-8329-f62d4b0e9a47"  # Replace with your actual access key
    token = get_daily_token(access_key)
    if not token:
        logging.error("Failed to fetch carpark season data due to token retrieval failure.")
        return []
    
    url = "https://www.ura.gov.sg/uraDataService/invokeUraDS?service=Season_Car_Park_Details"
    headers = {
        "AccessKey": access_key,
        "Token": token,
        "User-Agent": "MyApp/1.0",
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200 and response.headers.get('Content-Type') == 'application/json':
        return response.json().get("Result", [])
    else:
        logging.error(f"Failed to fetch carpark season data, status code: {response.status_code}, response: {response.text}")
        return []

def insert_carpark_season(season_data):
    for item in season_data:
        ppCode = item.get("ppCode")
        season = Season.query.filter_by(ppCode=ppCode).first()
        # Safely handle geometries list to avoid IndexError
        geometries = item.get("geometries", [{}])  # Keep as list of dictionaries
        coordinates = geometries[0].get("coordinates", "0,0") if geometries else "0,0"

        if season:
            # Update existing record
            season.ppName = item.get("ppName")
            season.vehCat = item.get("vehCat")
            season.monthlyRate = item.get("monthlyRate")
            season.coordinates = geometries[0].get("coordinates", "0,0") if geometries else "0,0"
            season.parkingHrs = item.get("parkingHrs")
            season.ticketType = item.get("ticketType")
        else:
            # Insert new record
            new_season = Season(
                ppCode=ppCode,
                ppName=item.get("ppName"),
                vehCat=item.get("vehCat"),
                monthlyRate=item.get("monthlyRate"),
                geometries=geometries,
                parkingHrs=item.get("parkingHrs"),
                ticketType=item.get("ticketType"),
            )
            db.session.add(new_season)
    db.session.commit()

@app.route("/update_carparks_lotsAvailability")
def update_carparks_lotsAvailability():
    lots_data = fetch_carpark_lotsAvailability()
    if lots_data:
        insert_carpark_lotsAvailability(lots_data)
        return jsonify({"message": "Carpark lots data updated successfully."}), 200
    else:
        return jsonify({"message": "Failed to fetch or update carpark lots data."}), 500
    
@app.route("/carparks_lotsAvailability")
def get_lotsAvailability():
    lotsAvailabilityList = db.session.scalars(db.select(Lots)).all()

    if len(lotsAvailabilityList):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "carparks": [lotsAvailability.json() for lotsAvailability in lotsAvailabilityList]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no carpark lots data."
        }
    ), 404

@app.route("/update_carparks_prices")
def update_carparks_prices():
    prices_data = fetch_carpark_prices()
    if prices_data:
        insert_carpark_prices(prices_data)
        return jsonify({"message": "Carpark prices updated successfully."}), 200
    else:
        return jsonify({"message": "Failed to fetch or update carpark prices."}), 500
    
@app.route("/carparks_prices")
def get_carpark_prices():
    prices_list = Prices.query.all()
    if prices_list:
        return jsonify({
            "code": 200,
            "data": [price.json() for price in prices_list]
        }), 200
    else:
        return jsonify({
            "code": 404,
            "message": "No carpark prices found."
        }), 404

@app.route("/update_carparks_season")
def update_carparks_season():
    season_data = fetch_carpark_season()
    if season_data:
        insert_carpark_season(season_data)
        return jsonify({"message": "Carpark season data updated successfully."}), 200
    else:
        return jsonify({"message": "Failed to fetch or update carpark season data."}), 500
    
@app.route("/carparks_season")
def get_carpark_season():
    season_list = Season.query.all()
    if season_list:
        return jsonify({
            "code": 200,
            "data": [season.json() for season in season_list]
        }), 200
    else:
        return jsonify({
            "code": 404,
            "message": "No carpark season data found."
        }), 404

@app.route("/carpark/getAll")
def get_all_carparks():
    lotsAvailabilityList = db.session.scalars(db.select(Lots)).all()
    pricesList = Prices.query.all()
    seasonList = Season.query.all()

    if len(lotsAvailabilityList) and len(pricesList) and len(seasonList):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "lotsAvailability": [lotsAvailability.json() for lotsAvailability in lotsAvailabilityList],
                    "prices": [price.json() for price in pricesList],
                    "season": [season.json() for season in seasonList]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no carpark data."
        }
    ), 404
 
@app.route("/carpark/<string:carparkNo>")
def find_by_id(carparkNo):
    lotsAvailability = db.session.scalars(
        db.select(Lots).filter_by(carparkNo=carparkNo).limit(1)
    ).first()

    if lotsAvailability:
        return jsonify(
            {
                "code": 200,
                "data": lotsAvailability.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "Carpark not found."
        }
    ), 404
    
# Adjust the create_carpark function to match the new data structure
@app.route("/carpark/<string:carparkNo>", methods=['POST'])
def create_carpark(carparkNo):
    if (db.session.scalars(
        db.select(Lots).filter_by(carparkNo=carparkNo).
        limit(1)
    ).first()):
        return jsonify(
            {
                "code": 400,
                "data": {
                    "carparkNo": carparkNo
                },
                "message": "Carpark already exists."
            }
        ), 400

    data = request.get_json()
    lotsAvailability = Lots(carparkNo, **data)

    try:
        db.session.add(lotsAvailability)
        db.session.commit()
    except:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "carparkNo": carparkNo
                },
                "message": "An error occurred creating the carpark."
            }
        ), 500

    return jsonify(
        {
            "code": 201,
            "data": lotsAvailability.json()
        }
    ), 201

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(port=5001, debug=True)