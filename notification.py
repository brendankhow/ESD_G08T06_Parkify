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
import pytz

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
TWILIO_ACCOUNT_SID = 'ACe015a2003e0631d5fd21582977238a35'
TWILIO_AUTH_TOKEN = 'dd76494b031d076c0f94b4ebee02af46'
TWILIO_PHONE_NUMBER = '+12054635814'
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
def notify_users():
    with app.app_context():
         # Use invoke_http to fetch carpark details
        response = requests.get(carpark_URL)
        if response.status_code != 200:
            # Handle the case where the request fails
            return jsonify({"error": "Failed to retrieve data from the external API"}), 500

        consolidated_data = response.json()  # Access the list of car park data
        
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

def schedule_notification_delayed():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=notify_users, trigger='date', run_date=datetime.now() + timedelta(minutes=1), timezone=pytz.timezone('Asia/Singapore'))
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
    schedule_notification_delayed()
    app.run(host='0.0.0.0', port=5004, debug=True)