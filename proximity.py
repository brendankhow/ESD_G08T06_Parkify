from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import googlemaps
import time

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:8889/location'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

def fetch_carpark_coordinates(location):
    # Clear previous search results
    db.session.query(Location).delete()
    db.session.commit()


    API_KEY = 'AIzaSyBx3sJpEQFY3o-4VYkT7Zfcwh8OABpTS-s'
    map_client = googlemaps.Client(API_KEY)

    address = location
    geocode = map_client.geocode(address=address)
    (lat, lng) = map(geocode[0]['geometry']['location'].get, ('lat', 'lng'))
    search_string = 'parking'
    distance = 3.21869
    business_list = []

    response = map_client.places_nearby(
        location=(lat, lng),
        keyword=search_string,
        radius=distance
    )

    business_list.extend(response.get('results'))
    next_page_token = response.get('next_page_token')

    while next_page_token:
        time.sleep(2)
        response = map_client.places_nearby(
            location=(lat, lng),
            keyword=search_string,
            radius=distance,
            page_token=next_page_token
        )
        business_list.extend(response.get('results'))
        next_page_token = response.get('next_page_token')

    for result in business_list:
        carpark_name = result['name']
        location = result['geometry']['location']
        coordinates = f"{location['lat']},{location['lng']}"
        # Check if car park exists, update if it does, otherwise insert new
        carpark = Location.query.get(carpark_name)
        if carpark:
            carpark.coordinates = coordinates
        else:
            new_carpark = Location(carparkName=carpark_name, coordinates=coordinates)
            db.session.add(new_carpark)
    db.session.commit()

@app.route("/locations/update")
def update_carpark_locations():
    fetch_carpark_coordinates()
    return jsonify({"message": "Carpark locations updated successfully."}), 200

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
    app.run(host='0.0.0.0', port=4001, debug=True)





