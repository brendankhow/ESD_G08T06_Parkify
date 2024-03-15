-- Create a new database
CREATE DATABASE IF NOT EXISTS users_db;

-- Use the newly created database
USE users_db;

-- Create a table to store user data
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    favourite VARCHAR(255) NOT NULL
);

-- Insert the provided data into the users table
INSERT INTO users (username, email, favourite)
VALUES 
    ('1', '1@gmail.com', 'A0004'),
    ('2', '2@gmail.com', 'A0004'),
    ('1', '1@gmail.com', 'A0005'),
    ('2', '2@gmail.com', 'A0005'),
    ('1', '1@gmail.com', 'A0006');
