import MySQLdb as mc
from runenv import load_env
import os
load_env()

user= os.environ.get('user')
host= os.environ.get('host')
passwd= os.environ.get('passwd')
database= os.environ.get('database')
mydb = mc.connect(host,user,passwd,database)
mycursor = mydb.cursor()
mycursor1 = mydb.cursor()


mycursor.execute("CREATE TABLE users (name VARCHAR(255) primary key, password VARCHAR(255),amount INTEGER default 1000,email VARCHAR(255))")
mycursor.execute("CREATE TABLE vehicles (number_plate VARCHAR(12) primary key,model_name VARCHAR(255),availabity VARCHAR(255),check ((availablity like '%YES%') OR (availablity like '%NO%')))")
mycursor.execute("CREATE TABLE station (station_id INT AUTO_INCREMENT PRIMARY KEY,station_name VARCHAR(30),latitude DECIMAL(6,4),longtitude DECIMAL(6,4),vehicle_count INTEGER,supply_limit INTEGER,demand_limit INTEGER)")
mycursor.execute("CREATE TABLE location (number_plate VARCHAR(12),station_id INT, FOREIGN KEY(number_plate) REFERENCES vehicles(number_plate),FOREIGN KEY(station_id) REFERENCES station(station_id))")
mycursor.execute("CREATE TABLE booking (name varchar(255) PRIMARY KEY,number_plate VARCHAR(12),otp INTEGER, time DATETIME,trip_mode varchar(20),FOREIGN KEY(number_plate) REFERENCES vehicles(number_plate),FOREIGN KEY(name) REFERENCES users(name))")
mycursor.execute("CREATE TABLE agent (name VARCHAR(255) primary key, password VARCHAR(255),station_id INTEGER,FOREIGN KEY(station_id) REFERENCES station(station_id))")

mydb=mysql.connector.connect(**config)
mycursor = mydb.cursor(buffered=True)
mycursor1 = mydb.cursor(buffered=True)
mycursor.execute('SHOW TABLES')
for x in mycursor:
     print(x[0].decode('utf-8'))
     query="SHOW COLUMNS FROM "+x[0].decode('utf-8')
     mycursor1.execute(query)
     for y in mycursor1:
             print(y)