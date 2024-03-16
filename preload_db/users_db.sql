-- Create a new database
CREATE DATABASE IF NOT EXISTS users_db;

-- Use the newly created database
USE users_db;

-- Create a table to store user data with the new table name
CREATE TABLE IF NOT EXISTS users_fav_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    favourite VARCHAR(255) NOT NULL
);

-- Create a table to store user information (username and email)
CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    PRIMARY KEY (username, email)
);

-- Insert the provided data into the users_fav_table table
INSERT INTO users_fav_table (username, email, favourite)
VALUES 
    ('1', '1@gmail.com', 'A0004'),
    ('2', '2@gmail.com', 'A0004'),
    ('1', '1@gmail.com', 'A0005'),
    ('2', '2@gmail.com', 'A0005'),
    ('1', '1@gmail.com', 'A0006');
