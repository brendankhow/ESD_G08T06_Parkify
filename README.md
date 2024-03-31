# :wave: ESD Project Parkify

<div align="center">
    <img src="/parkify.png" alt="Parkify Logo">
</div>

- Youtube Demo Link: <link>

## Table of Contents

- [Group Members](#group-members)
- [Important Notes](#important-notes)
- [Project Overview](#project-overview)
  - [User Scenarios](#user-scenarios)
- [Installation Guide](#installation-guide)
  - [Project Setup](#project-setup)

## Group Members

---

| Name                | Student ID | Email                            |
| ------------------- | ---------- | -------------------------------- |
| Brendan Khow Bo Ren | 01415987   | brendankhow.2022@scis.smu.edu.sg |
| Lee Pei Yi          | 01466725   | peiyi.lee.2022@smu.edu.sg        |
| Liu Jia Hong        | 01449636   | jiahong.liu.2022@scis.smu.edu.sg |
| Teo Jia Xuan Ryan   | 01420283   | ryan.teo.2022@scis.smu.edu.sg    |
| Zia Kok Nuan Fei    | 01463932   | nuanfei.kok.2022@scis.smu.edu.sg |

---

## Project Overview

Parkify is a car parking app designed to streamline the parking process.

### User Scenarios

1. **Users search for a carpark:**

   - They can search for a specific location, say “Old Airport Road”, and from there, our application will generate a list of top 10 car parks that are closest to their searched location.

2. **Users add a car park to their favourites list:**

   - For car parks that users visit frequently, they can ‘favourite’ it, or ‘unfavourite’ it if they wish to remove it from the list.

3. **Users receive notifications of their favourite car parks:**

   - Our web application sends notifications to users at a set time every day to alert them of lots availability as well as the car park prices to their mobile phones via SMS.

---

## Installation Guide

### Project Setup

1. **Import database into MySQL:**
   - Import all 3 sql file into MySQL.
      1. carpark.sql
      2. location.sql
      3. users_db.sql
2. **Ensure everything is installed:**
   - Run `pip install -r requirements.txt` in terminal.

3. **Docker Setup:**
   - Open Docker Desktop application.
   - Build Docker images: Run `chmod +x build.sh` and then `./build.sh` in terminal.

4. **Running of website:**
   - Docker run: Run `docker compose up` in terminal.

5. **Setting up frontend**
   - Open MAMP/WAMP application.
   - Copy 5 files into MAMP/WAMP directory.
      1. check_users.php
      2. frontend.html
      3. login.html
      4. parkify.mp4
      5. parkify.png
   - Open login.html in browser.