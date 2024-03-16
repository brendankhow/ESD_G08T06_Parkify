-- Create a new database
CREATE DATABASE IF NOT EXISTS users_db;

-- Use the newly created database
USE users_db;

-- Create a table to store user data with the new table name
CREATE TABLE IF NOT EXISTS users_fav_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    favourite VARCHAR(255) NOT NULL
);

-- Create a table to store user information (username and email)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) NOT NULL
);
