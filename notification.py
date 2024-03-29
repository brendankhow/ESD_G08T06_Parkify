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

def notify_new_entries():
    with app.app_context():
        # Check for new entries in the database
        new_entries = UserFavourite.query.filter_by(notified=False).all()
        
        for entry in new_entries:
            # Send notification
            send_notification(entry)

            # Mark entry as notified
            entry.notified = True
            db.session.commit()

def send_notification(entry):
    # Construct message
    message = f"New entry added:\nUsername: {entry.username}\nEmail: {entry.email}\nPhone Number: {entry.phone_number}\nFavorite: {entry.favourite}"

    # Send SMS
    send_sms(entry.phone_number, message)

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
            connection.execute(text("CREATE TABLE IF NOT EXISTS users_fav_table (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255) NOT NULL, email VARCHAR(255) NOT NULL, phone_number VARCHAR(20) NOT NULL, favourite VARCHAR(255) NOT NULL, notified BOOLEAN DEFAULT FALSE)"))
            connection.execute(text("CREATE TABLE IF NOT EXISTS users (username VARCHAR(255) NOT NULL, email VARCHAR(255) NOT NULL, phone_number VARCHAR(20) NOT NULL, PRIMARY KEY (username, email))"))
        db.create_all()

        # Schedule job to notify about new entries every 2 minutes
        scheduler = BackgroundScheduler()
        scheduler.add_job(func=notify_new_entries, trigger='interval', minutes=2)
        scheduler.start()

    app.run(host='0.0.0.0', port=5004, debug=True)