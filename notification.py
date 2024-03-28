from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import create_engine, text
from os import environ
from invokes import invoke_http
# scheduler
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from requests import get
import requests

from twilio.rest import Client

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:8889/users_db'
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

carpark_URL = environ.get('carpark_URL') or "http://localhost:5001/consolidated"

db = SQLAlchemy(app)

CORS(app)

# Twilio settings
TWILIO_ACCOUNT_SID = 'AC4c2f5867563167ee03c132d8ca8086fb'
TWILIO_AUTH_TOKEN = '87044ecdb00c7cfd9ac8edc1f013656f'
TWILIO_PHONE_NUMBER = '+15642242132'
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

# Define a flag to indicate whether the notify_users function is currently running
notify_users_running = False

@app.route("/notify_users")
def trigger_notify_users():
    global notify_users_running
    # Check if notify_users is already running
    if notify_users_running:
        return jsonify({"message": "notify_users is already running"}), 400
    # Set the flag to indicate that notify_users is running
    notify_users_running = True
    # Execute the notify_users function
    message, status_code = notify_users()
    # Reset the flag after execution
    notify_users_running = False
    return message, status_code

def notify_users():
    with app.app_context():
         # Use invoke_http to fetch carpark details
        response = invoke_http(carpark_URL, method='GET')
        
        # Check if the request was successful
        if response['code'] != 200:
            print("Error fetching carpark details")
            return jsonify({"message": "Error fetching carpark details"}), 500
        consolidated_data = response['data']  # Assuming the response structure has a 'data' key with the required information

        users = UserFavourite.query.all()
        for user in users:
            if user.phone_number and user.favourite:
                fav_carparks = user.favourite.split(',')
                messages = []

                for fav in fav_carparks:
                    carpark_details = consolidated_data.get(fav)
                    if carpark_details:
                        car_details = carpark_details.get('vehicles', {}).get('Car', {})
                        lots_available = car_details.get('lotsAvailable', 'N/A')
                        pricing = car_details.get('pricing', {})
                        start_times = pricing.get('startTime', [])
                        end_times = pricing.get('endTime', [])
                        rates = pricing.get('weekdayRate', [])

                        if len(start_times) == len(end_times) == len(rates):
                            message = f"Carpark {fav}: Available - {lots_available}, Rates:\n"
                            for i in range(len(start_times)):
                                message += f"{start_times[i]} to {end_times[i]} - {rates[i]}\n"
                            messages.append(message)
                        else:
                            messages.append(f"Carpark {fav} details not found.")
                    else:
                        messages.append(f"Carpark {fav} details not found.")

                send_sms(user.phone_number, "\n".join(messages))
        return jsonify({"message": "SMS notifications sent successfully"}), 200

def schedule_daily_notifications():
    scheduler = BackgroundScheduler()
    # scheduler.add_job(func=trigger_notify_users, trigger='cron', hour=10)
    scheduler.add_job(func=trigger_notify_users, trigger='cron', hour=10, timezone=pytz.timezone('Asia/Singapore'))
    scheduler.start()

def send_sms(to, message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    client.messages.create(
        to=to,
        from_=TWILIO_PHONE_NUMBER,
        body=message
    )

if __name__ == '__main__':
    with app.app_context():
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        with engine.connect() as connection:
            connection.execute(text("CREATE DATABASE IF NOT EXISTS users_db"))
            connection.execute(text("USE users_db"))
            connection.execute(text("CREATE TABLE IF NOT EXISTS users_fav_table (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255) NOT NULL, email VARCHAR(255) NOT NULL, phone_number VARCHAR(20) NOT NULL, favourite VARCHAR(255) NOT NULL)"))
            connection.execute(text("CREATE TABLE IF NOT EXISTS users (username VARCHAR(255) NOT NULL, email VARCHAR(255) NOT NULL, phone_number VARCHAR(20) NOT NULL, PRIMARY KEY (username, email))"))
        db.create_all()
    schedule_daily_notifications()
    app.run(host='0.0.0.0', port=5004, debug=True)