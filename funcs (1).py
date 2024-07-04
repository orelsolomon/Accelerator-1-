import mysql.connector
from mysql.connector import Error
from datetime import datetime
import requests
import db_lib

GET_CITY_QUERY = "SELECT city FROM customerPlants WHERE plant_ID = %s"
GET_PLANT_FAMILY_QUERY = "SELECT family_fk FROM customerPlants WHERE plant_ID = %s"
GET_REQ_MOISTURE_QUERY = "SELECT soil_moisture FROM plantFamily WHERE family = %s AND temp = %s"

UPDATE_REQUIRED_SOIL_MOISTURE_QUERY = "UPDATE required_soil_moisture SET is_current = 0 WHERE is_current = 1 AND plant_id = %s"
SET_REQUIRED_SOIL_MOISTURE_QUERY = "INSERT INTO required_soil_moisture (plant_id, calculation_time, calculation_date, required_moisture) VALUES (%s, %s, %s, %s)"

def get_city_by_plant_id(connection, plant_id):
    record = db_lib.get_single_result_from_query(connection, GET_CITY_QUERY, plant_id)
    if record:
        return record
    else:
        print(f"No city found for plant_ID: {plant_id}")
        return None

def get_plant_family_from_id(connection, plant_id):
    return db_lib.get_single_result_from_query(connection, GET_PLANT_FAMILY_QUERY, plant_id)

def get_required_soil_moisture_for_plant_family_and_temperature(connection, plant_family, temperature):
    return db_lib.get_single_result_from_query(connection, GET_REQ_MOISTURE_QUERY, plant_family, temperature)

def get_temp_by_city(city):
    api_key = "f3fac4d11d4747f8a59132627240605"  # Your WeatherAPI API key
    url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}&aqi=no"
    response = requests.get(url)
    data = response.json()
    if "error" not in data:
        temperature = data["current"]["temp_c"]  # Access temperature in Celsius
        return temperature
    else:
        print(f"Error fetching weather data for city: {city}")
        return None

def set_required_soil_moisture(connection, plant_id, required_moisture):
    cursor = connection.cursor()
    try:
        cursor.execute(UPDATE_REQUIRED_SOIL_MOISTURE_QUERY, (plant_id,))
        
        now = datetime.now()
        calculation_date = now.strftime('%Y-%m-%d')
        calculation_time = now.strftime('%H:%M:%S')
        data_tuple = (plant_id, calculation_time, calculation_date, required_moisture)
        cursor.execute(SET_REQUIRED_SOIL_MOISTURE_QUERY, data_tuple)
        connection.commit()
        print("Data inserted successfully into required_soil_moisture table")
    except mysql.connector.Error as error:
        print(f"Failed to insert into MySQL table: {error}")
    finally:
        cursor.close()

if __name__ == "__main__":
    plant_id = 4
    connection = db_lib.get_db_connection()

    if connection is None:
        print("Failed to connect to the database.")
        exit()

    city = get_city_by_plant_id(connection, plant_id)

    if city is None:
        print("City not found for the given plant ID.")
        connection.close()
        exit()

    temperature = get_temp_by_city(city)

    if temperature is None:
        print("Failed to get temperature data.")
        connection.close()
        exit()

    plant_family = get_plant_family_from_id(connection, plant_id)

    if plant_family is None:
        print("Failed to get plant_family data.")
        connection.close()
        exit()

    required_moisture = get_required_soil_moisture_for_plant_family_and_temperature(connection, plant_family, temperature)
    
    if required_moisture is None:
        print("Failed to get required_moisture data.")
        connection.close()
        exit()
    
    set_required_soil_moisture(connection, plant_id, required_moisture)

    connection.close()
