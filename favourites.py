from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import create_engine, text

# users.py - Add these imports at the top
from sms_service import send_sms
# scheduler
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from requests import get
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:8889/users_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

CORS(app)

class UserFavourite(db.Model):
    __tablename__ = 'users_fav_table'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    favourite = db.Column(db.String(255), nullable=False)

    def __init__(self, username, email, phone_number, favourite):
        self.username = username
        self.email = email
        self.phone_number = phone_number
        self.favourite = favourite


@app.route("/users")
def get_all_users():
    users = UserFavourite.query.order_by(UserFavourite.username, UserFavourite.email).all()
    if users:
        formatted_users = [
            {
                'username': user.username,
                'email': user.email,
                'favourite': user.favourite,
                'phone_number': user.phone_number  # Include the phone number in the response
            } for user in users
        ]
        return jsonify({"code": 200, "data": {"users": formatted_users}})
    return jsonify({"code": 404, "message": "There are no users."}), 404

@app.route("/users_fav")
def get_all_user_favourites():
    favourites = UserFavourite.query.all()
    if favourites:
        formatted_favourites = [{'id': fav.id, 'username': fav.username, 'email': fav.email, 'phone_number': fav.phone_number, 'favourite': fav.favourite} for fav in favourites]
        return jsonify({"code": 200, "data": {"favourites": formatted_favourites}})
    return jsonify({"code": 404, "message": "There are no favourites."}), 404

@app.route("/users_fav_table/<username>")
def get_user_favourites(username):
    user_favourites = UserFavourite.query.filter_by(username=username).all()
    if user_favourites:
        formatted_favourites = [{'username': fav.username, 'favourite': fav.favourite} for fav in user_favourites]
        return jsonify({"code": 200, "data": {"favourites": formatted_favourites}})
    return jsonify({"code": 404, "message": "User not found or has no favourites."}), 404

@app.route("/users_fav_table/<username>", methods=['POST'])
def add_user_favourite(username):
    data = request.json
    email = data.get('email')
    phone_number = data.get('phone_number')
    favourite = data.get('favourite')

    if not email or not phone_number or not favourite:
        return jsonify({"code": 400, "message": "Missing required fields."}), 400

    # Check if the favourite already exists for the user
    existing_favourite = UserFavourite.query.filter_by(username=username, favourite=favourite).first()
    if existing_favourite:
        return jsonify({"code": 409, "message": "Favourite already exists."}), 409

    # Create a new UserFavourite instance
    new_favourite = UserFavourite(username=username, email=email, phone_number=phone_number, favourite=favourite)

    # Add to the database session and commit
    db.session.add(new_favourite)
    db.session.commit()

    return jsonify({"code": 201, "message": "Favourite added successfully."}), 201

@app.route("/users_fav_table/<username>", methods=['DELETE'])
def remove_user_favourite(username):
    data = request.json
    favourite = data.get('favourite')

    if not favourite:
        return jsonify({"code": 400, "message": "Missing 'favourite' field."}), 400

    # Check if the favourite exists for the user
    existing_favourite = UserFavourite.query.filter_by(username=username, favourite=favourite).first()
    if not existing_favourite:
        return jsonify({"code": 404, "message": "Favourite not found."}), 404

    # Remove the favourite from the database
    db.session.delete(existing_favourite)
    db.session.commit()

    return jsonify({"code": 200, "message": "Favourite removed successfully."}), 200

# Modify your existing notify_users function
@app.route("/notify_users")
# This function will be triggered by the scheduler every day at 10 AM
def notify_users():
    with app.app_context():
        # Get all carparks details first
        response = requests.get('http://localhost:5001/getAllCarparks')
        if response.status_code != 200:
            print("Error fetching carpark details")
            return
        all_carparks_data = response.json()['data']
        
        users = UserFavourite.query.all()
        for user in users:
            if user.phone_number and user.favourite:
                fav_carparks = user.favourite.split(',')
                messages = []

                # Match user's favorite carparks with the ones in the all_carparks_data
                for fav in fav_carparks:
                    carpark_details = next((item for item in all_carparks_data if item['ppCode'] == fav), None)
                    if carpark_details:
                        message = (f"Carpark {carpark_details['ppCode']}: Available - {carpark_details.get('lotsAvailable', 'N/A')}, "
                                f"Rate - {carpark_details.get('weekdayRate', 'N/A')} from {carpark_details.get('startTime', 'N/A')} "
                                f"to {carpark_details.get('endTime', 'N/A')}")
                        messages.append(message)
                    else:
                        messages.append(f"Carpark {fav} details not found.")

                # Send a single SMS with all favorites information
                send_sms(user.phone_number, " ".join(messages))

# Create a scheduled job to notify users
def schedule_daily_notifications():
    scheduler = BackgroundScheduler()
    # scheduler.add_job(func=notify_users, trigger="cron", hour=10)
    # for testing if scheduler works NOW rather than wait for 10am
    scheduler.add_job(func=notify_users, trigger='date', run_date=datetime.now() + timedelta(seconds=30))  # to run 30 seconds from now
    scheduler.start()

# Call this function somewhere in your users.py file to start the scheduler
schedule_daily_notifications()


# Register routes and start the scheduler
if __name__ == '__main__':
    with app.app_context():
        engine = create_engine('mysql+mysqlconnector://root:root@localhost:8889')
        with engine.connect() as connection:
            connection.execute(text("CREATE DATABASE IF NOT EXISTS users_db"))
            connection.execute(text("USE users_db"))
            connection.execute(text("CREATE TABLE IF NOT EXISTS users_fav_table (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255) NOT NULL, email VARCHAR(255) NOT NULL, phone_number VARCHAR(20) NOT NULL, favourite VARCHAR(255) NOT NULL)"))
            connection.execute(text("CREATE TABLE IF NOT EXISTS users (username VARCHAR(255) NOT NULL, email VARCHAR(255) NOT NULL, phone_number VARCHAR(20) NOT NULL, PRIMARY KEY (username, email))"))
        db.create_all()
    schedule_daily_notifications()
    app.run(host='0.0.0.0', port=5003, debug=True)

