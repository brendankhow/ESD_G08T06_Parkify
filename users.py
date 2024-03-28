from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import create_engine, text
from os import environ

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:8889/users_db'
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

CORS(app)

class User(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String(255), primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)

    def __init__(self, username, email, phone_number):
        self.username = username
        self.email = email
        self.phone_number = phone_number


@app.route("/registered_users")
def get_registered_users():
    users = User.query.all()
    if users:
        formatted_users = [{'username': user.username, 'email': user.email, 'phone_number': user.phone_number} for user in users]
        return jsonify({"code": 200, "data": {"users": formatted_users}})
    return jsonify({"code": 404, "message": "There are no registered users."}), 404

if __name__ == '__main__':
    with app.app_context():
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        with engine.connect() as connection:
            connection.execute(text("CREATE DATABASE IF NOT EXISTS users_db"))
            connection.execute(text("USE users_db"))
            connection.execute(text("CREATE TABLE IF NOT EXISTS users_fav_table (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255) NOT NULL, email VARCHAR(255) NOT NULL, phone_number VARCHAR(20) NOT NULL, favourite VARCHAR(255) NOT NULL)"))
            connection.execute(text("CREATE TABLE IF NOT EXISTS users (username VARCHAR(255) NOT NULL, email VARCHAR(255) NOT NULL, phone_number VARCHAR(20) NOT NULL, PRIMARY KEY (username, email))"))
        db.create_all()
    app.run(host='0.0.0.0', port=5002, debug=True)
