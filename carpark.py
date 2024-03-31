from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import environ
import requests
import logging
from sqlalchemy import create_engine, text

app = Flask(__name__)
CORS(app)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:3306/carpark?charset=utf8'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:8889/carpark'
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Lots(db.Model): 
    __tablename__ = 'lots'
    ppCode = db.Column(db.String(5), primary_key=True)
    coordinates = db.Column(db.String(50))  # Changed to String to match your data format
    lotsAvailable = db.Column(db.Integer, nullable=False)
    lotType = db.Column(db.String(1), nullable=False)

    def __init__(self, ppCode, geometries, lotsAvailable, lotType):
        self.ppCode = ppCode
        # self.coordinates = geometries[0]['coordinates'] if geometries else None  # Assuming the first geometry is what you want
        self.coordinates = geometries[0].get('coordinates', '0,0') if geometries else '0,0'
        self.lotsAvailable = lotsAvailable
        self.lotType = lotType

    def json(self):
        return {"ppCode": self.ppCode, "coordinates": self.coordinates, "lotsAvailable": self.lotsAvailable, "lotType": self.lotType}

class Prices(db.Model):
    __tablename__ = 'prices'
    id = db.Column(db.Integer, primary_key=True)  # New auto-incrementing ID field
    ppCode = db.Column(db.String(5))
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

def fetch_carpark_lots():
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
        result = response.json().get("Result", [])
        print(f"Number of lines in the result: {len(result)}")
        return result
    else:
        logging.error(f"Failed to fetch carpark lots data, status code: {response.status_code}, response: {response.text}")
        return []

    
def insert_carpark_lots(lots_data):
    for item in lots_data:
        ppCode = item.get("carparkNo")
        lotType = item.get("lotType")
        lotsAvailable = int(item.get("lotsAvailable"))
        geometries = item.get("geometries", [{}])  # Keep as list of dictionaries

        # Check if carpark already exists to update or insert new
        lots = Lots.query.filter_by(ppCode=ppCode).first()
        if lots:
            lots.coordinates = geometries[0].get("coordinates", "0,0") if geometries else "0,0"
            lots.lotsAvailable = lotsAvailable
            lots.lotType = lotType
            # Assuming the first geometry's coordinates is what you want
  
        else:
            # Correctly pass geometries to the constructor
            lots = Lots(ppCode=ppCode, geometries=geometries, lotsAvailable=lotsAvailable, lotType=lotType)
            db.session.add(lots)
    
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
    # Check if the database is empty
    is_db_empty = Prices.query.first() is None

    for item in prices_data:
        ppCode = item.get("ppCode")
        startTime = item.get("startTime")
        endTime = item.get("endTime")
        vehCat=item.get("vehCat")
        # Safely handle geometries list to avoid IndexError
        geometries = item.get("geometries", [{}])  # Keep as list of dictionaries
        coordinates = geometries[0].get("coordinates", "0,0") if geometries else "0,0"

        if not is_db_empty:
            # Check for existing record
            # price = Prices.query.filter_by(ppCode=ppCode, startTime=startTime, endTime=endTime).first()
            price = Prices.query.filter_by(ppCode=ppCode, startTime=startTime, endTime=endTime, vehCat=vehCat).first()
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
                price.parkCapacity = item.get("parkCapacity")
                continue  # Skip to the next iteration

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
            startTime=startTime,
            parkCapacity=item.get("parkCapacity"),
            endTime=endTime
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

##### new restructure data function#######
def restructure_carpark_data(data, lots_data):
    # Initialize a dictionary to store the restructured data
    restructured_data = {}

    # Create a mapping dictionary for vehicle categories
    vehCat_map = {"C": "Car", "M": "Motorcycle", "H": "Heavy Vehicle"}

    # Iterate through each entry in the original data
    for entry in data:
        ppCode = entry['ppCode']
        ppName = entry['ppName']
        coordinates = entry['coordinates']
        parkingSystem = entry['parkingSystem']

        # If the ppCode is not in the restructured data, initialize its entry
        if ppCode not in restructured_data:
            restructured_data[ppCode] = {
                'ppName': ppName.strip(),  # Remove extra spaces from ppName
                'coordinates': coordinates,
                'parkingSystem': parkingSystem,
                'vehicles': {}
            }

        vehCat = entry['vehCat']
        parkCapacity = entry.get('parkCapacity', None)

        # If the vehicle category is not in the ppCode entry, initialize its entry
        if vehCat not in restructured_data[ppCode]['vehicles']:
            restructured_data[ppCode]['vehicles'][vehCat] = {
                'parkCapacity': parkCapacity,
                'lotsAvailable': None,  # Initialize lotsAvailable as None
                'pricing': {
                    'startTime': [],
                    'endTime': [],
                    'weekdayMin': [],
                    'weekdayRate': [],
                    'satdayMin': [],
                    'satdayRate': [],
                    'sunPHMin': [],
                    'sunPHRate': []
                }
            }

        # Check if the ppCode and lotType match in lots_data
        for lot in lots_data:
            if lot['ppCode'] == ppCode and vehCat_map.get(lot['lotType']) == vehCat:
                restructured_data[ppCode]['vehicles'][vehCat]['lotsAvailable'] = lot['lotsAvailable']

        pricing_info = restructured_data[ppCode]['vehicles'][vehCat]['pricing']
        pricing_info['startTime'].append(entry.get('startTime', ""))
        pricing_info['endTime'].append(entry.get('endTime', ""))
        pricing_info['weekdayMin'].append(entry.get('weekdayMin', ""))
        pricing_info['weekdayRate'].append(entry.get('weekdayRate', ""))
        pricing_info['satdayMin'].append(entry.get('satdayMin', ""))
        pricing_info['satdayRate'].append(entry.get('satdayRate', ""))
        pricing_info['sunPHMin'].append(entry.get('sunPHMin', ""))
        pricing_info['sunPHRate'].append(entry.get('sunPHRate', ""))

    return restructured_data



############# updating carpark lots API ################
@app.route("/update_carparks_lots")
def update_carparks_lots():
    lots_data = fetch_carpark_lots()
    if lots_data:
        insert_carpark_lots(lots_data)
        return jsonify({"message": "Carpark lots data updated successfully."}), 200
    else:
        return jsonify({"message": "Failed to fetch or update carpark lots data."}), 500
       #### view carpark lot data ###
@app.route("/carparks_lots")
def get_carparks_lots():
    lotsList = db.session.scalars(db.select(Lots)).all()

    if len(lotsList):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "carparks": [lots.json() for lots in lotsList]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no carpark lots data."
        }
    ), 404

############# updating carpark prices API ################
@app.route("/update_carparks_prices")
def update_carparks_prices():
    prices_data = fetch_carpark_prices()
    if prices_data:
        insert_carpark_prices(prices_data)
        return jsonify({"message": "Carpark prices updated successfully."}), 200
    else:
        return jsonify({"message": "Failed to fetch or update carpark prices."}), 500

    #### view carpark prices data ###
@app.route("/carparks_prices")
def get_carparks_prices():
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

############# updating season carpark API ################
@app.route("/update_carparks_season")
def update_carparks_season():
    season_data = fetch_carpark_season()
    if season_data:
        insert_carpark_season(season_data)
        return jsonify({"message": "Carpark season data updated successfully."}), 200
    else:
        return jsonify({"message": "Failed to fetch or update carpark season data."}), 500

    #### view season carpark data ###
@app.route("/carparks_season")
def get_carparks_season():
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

############# updating all 3 information API ################
def update_all_carparks():
    update_carparks_lots()
    update_carparks_prices()
    update_carparks_season()
    db.session.commit()
    print("All carpark data updated successfully")

@app.route("/carparks/updateAll")
def update_all_carparks_route():
    update_all_carparks()
    return "All carpark data updated successfully", 200

@app.route("/carparks/getAll")
def get_all_carparks():
    lotsList = db.session.scalars(db.select(Lots)).all()
    pricesList = Prices.query.all()
    seasonList = Season.query.all()

    if len(lotsList) and len(pricesList) and len(seasonList):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "lots": [lots.json() for lots in lotsList],
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
    #### view combined carpark data ###
@app.route("/getAllCarparks")
def get_all():
    lotsList = db.session.scalars(db.select(Lots)).all()
    pricesList = Prices.query.all()
    seasonList = Season.query.all()

    combinedData = []

    if len(lotsList) and len(pricesList) and len(seasonList):
        for price in pricesList:
            lot = next((lot for lot in lotsList if lot.ppCode == price.ppCode), None)
            season = next((season for season in seasonList if season.ppCode == price.ppCode), None)

            combinedItem = price.json()
            if lot is not None:
                combinedItem.update(lot.json())
            if season is not None:
                combinedItem.update(season.json())

            combinedData.append(combinedItem)

        return jsonify(
            {
                "code": 200,
                "data": combinedData
            }
        )

    return jsonify(
        {
            "code": 404,
            "message": "There are no carpark data."
        }
    ), 404

######### new consolidated restructure data ######
@app.route("/consolidated")
def get_consolidated_data():
    # Directly call get_all function and get its response data
    combinedData_response = get_all()
    combinedData_json = combinedData_response.get_json()

    if combinedData_json['code'] != 200:
        return jsonify({"message": "Failed to fetch carpark data from /getAllCarparks."}), 500

    carpark_data = combinedData_json.get("data", [])

    # Fetch data from /carparks_lots
    lots_response = get_carparks_lots()
    lots_json = lots_response.get_json()

    if lots_json['code'] != 200:
        return jsonify({"message": "Failed to fetch carpark lots data from /carparks_lots."}), 500

    lots_data = lots_json.get("data", {}).get("carparks", [])

    # Restructure the carpark data
    restructured_data = restructure_carpark_data(carpark_data, lots_data)

    return jsonify(restructured_data), 200

with app.app_context():
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    with engine.connect() as connection:
        connection.execute(text("CREATE DATABASE IF NOT EXISTS carpark"))
    db.create_all()
    update_all_carparks()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)











