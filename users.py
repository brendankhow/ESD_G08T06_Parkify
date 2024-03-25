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
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/users_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

CORS(app)

class User(db.Model):
    __tablename__ = 'users_fav_table'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)  # New column
    favourite = db.Column(db.String(255), nullable=False)
    # adding a phone_number field
    phone_number = db.Column(db.String(255))  # Make sure this matches your database schema


    def __init__(self, username, email, favourite, phone_number=None):
        self.username = username
        self.email = email
        self.phone_number = phone_number
        self.favourite = favourite
        self.phone_number = phone_number


@app.route("/users")
def get_all_users():
    users = User.query.order_by(User.username, User.email).all()
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

@app.route("/users_fav_table/<username>")
def get_user_favourites(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({"code": 200, "data": {"favourites": user.favourite}})
    return jsonify({"code": 404, "message": "User not found."}), 404




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
        
        users = User.query.all()
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
        engine = create_engine('mysql+mysqlconnector://root:root@localhost:3306')
        with engine.connect() as connection:
            connection.execute(text("CREATE DATABASE IF NOT EXISTS users_db"))
            connection.execute(text("USE users_db"))
            connection.execute(text("CREATE TABLE IF NOT EXISTS users_fav_table (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255) NOT NULL, email VARCHAR(255) NOT NULL, phone_number VARCHAR(20) NOT NULL, favourite VARCHAR(255) NOT NULL)"))
            connection.execute(text("CREATE TABLE IF NOT EXISTS users (username VARCHAR(255) NOT NULL, email VARCHAR(255) NOT NULL, phone_number VARCHAR(20) NOT NULL, PRIMARY KEY (username, email))"))
        db.create_all()
    schedule_daily_notifications()
    app.run(host='0.0.0.0', port=5002, debug=True)
