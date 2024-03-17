from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import create_engine, text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:3306/users_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

CORS(app)

class User(db.Model):
    __tablename__ = 'users_fav_table'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    favourite = db.Column(db.String(255), nullable=False)

    def __init__(self, username, email, favourite):
        self.username = username
        self.email = email
        self.favourite = favourite

@app.route("/users")
def get_all_users():
    users = User.query.order_by(User.username, User.email).all()
    if users:
        formatted_users = [{'username': user.username, 'email': user.email, 'favourite': user.favourite} for user in users]
        return jsonify({"code": 200, "data": {"users": formatted_users}})
    return jsonify({"code": 404, "message": "There are no users."}), 404

@app.route("/users_fav_table/<username>")
def get_user_favourites(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({"code": 200, "data": {"favourites": user.favourite}})
    return jsonify({"code": 404, "message": "User not found."}), 404

if __name__ == '__main__':
    with app.app_context():
        engine = create_engine('mysql+mysqlconnector://root:root@localhost:3306')
        with engine.connect() as connection:
            connection.execute(text("CREATE DATABASE IF NOT EXISTS users_db"))
            connection.execute(text("USE users_db"))
            connection.execute(text("CREATE TABLE IF NOT EXISTS users_fav_table (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255) NOT NULL, email VARCHAR(255) NOT NULL, favourite VARCHAR(255) NOT NULL)"))
            connection.execute(text("CREATE TABLE IF NOT EXISTS users (username VARCHAR(255) NOT NULL, email VARCHAR(255) NOT NULL, PRIMARY KEY (username, email))"))
        db.create_all()
    app.run(host='0.0.0.0', port=5002, debug=True)

