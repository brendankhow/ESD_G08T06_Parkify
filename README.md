# esd-group6

## Installation

1. Ensure everything is installed: Run `pip install -r requirements.txt` in terminal.

## Docker Setup

1. Build Docker images: Run `chmod +x build.sh` and then `./build.sh` in terminal.
2. Docker run: Run `docker compose up` in terminal.

## WATCH THE MAGIC

---------------------------------------------------------------------------------------------------------

## Pre-Run Setup

1. Change the port number to your MAMP port number.
2. Create a `carpark` database in MySQL.

## Running the Application

1. Run `python3 carpark.py`.

## Database Operations

1. To insert all data into the database: `/carparks/updateAll`.
2. To view all data in the webpage: `/carparks/getAll`.

## Carpark Lots

1. To insert into the database: `/update_carparks_lots`.
2. To view in JSON on the webpage: `/carparks_lots`.

## Carpark Prices

1. To insert into the database: `/update_carparks_prices`.
2. To view in JSON on the webpage: `/carparks_prices`.

## Carpark Season

1. To insert into the database: `/update_carparks_season`.
2. To view in JSON on the webpage: `/carparks_season`.

## User Data

1. Run `python3 users.py`.
2. To view user data: `/users`.

## Frontend Setup

1. Bring `login.html`, `check_user.php`, `frontend.html` to your localhost route to run from the server.
2. Make sure you change the port number in the address tab when it's open in Chrome.
3. `frontend.html` will be empty when you enter it as there is no username passed into it. Therefore, run `login.html` and login accordingly for it to lead to `frontend.html`.



What to do before running:
1) change port number to mamp port number
2) create carpaprk db in mysql

To run the file: run python3 carpark.py

To insert all data into db: /carparks/updateAll
To view all in webpage: /carparks/getAll


To view:
To insert into db: /update_carparks_lots
To view in json on webpage: /carparks_lots"

To insert into db: /update_carparks_prices
/To view in json on webpage:carparks_prices

To insert into db: /update_carparks_season
To view in json on webpage:/carparks_season

To view all in webpage: /carpark/getAll



run python3 users.py
To view user data: /users


Bring login.html, check_user.php, frontend.html to ur localhost route to run from server. 
Run from there, make sure u change check what's ur port number in address tab when it's open in chrome. 

Frontend.html will be empty when u enter it as there is no username passed into it therefore, run login.html and login accordingly for it to lead to frontend.html.

