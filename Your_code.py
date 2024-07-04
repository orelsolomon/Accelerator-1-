import mysql.connector
from datetime import datetime
from Moisture_Controller import MoistureController
import time
import db_lib
import requests

GET_REQUIRED_MOISTURE_VALUED_QUERY = "SELECT required_moisture FROM required_soil_moisture WHERE is_current = 1"
GET_CITY_QUERY = "SELECT city FROM customerPlants WHERE plant_ID = %s"

SET_SESNSOR_DATA_QUERY = "INSERT INTO sensor_data (plant_id, measurement_date, measurement_time, current_temp, current_soil_moisture) VALUES (%s, %s, %s, %s, %s)"
SET_IRRIGATION_QUERY = "INSERT INTO irrigation (plant_id, irrigation_date, irrigation_time) VALUES (%s, %s, %s)"

serial_port = 'COM3'  # Change this to the appropriate port
baud_rate = 9600
min_reading = 256  # digital units
max_reading = 557  # digital units (ביתים)
num_samples = 5
std_threshold = 1  # (סטיית גבול תקן)

irrigation = None  # This value will stay None if no irrigation was executed, or if irrigation was executed it will change to the last reading of the moisture sensor.

controller = MoistureController(serial_port, baud_rate, min_reading, max_reading, num_samples, std_threshold)

def get_required_moisture_value(connection):
    return db_lib.get_single_result_from_query(connection, GET_REQUIRED_MOISTURE_VALUED_QUERY)

def pump_water_if_needed(controller, Required_moisture_value, plant_id, temperature):
    Moisture_data_measured, mean_moisture_data = controller.read_moisture_sensor() # לוקח את הלחות מהסנסור

    controller.plot_readings(Moisture_data_measured, mean_moisture_data, Required_moisture_value) #יוצר את הגרף
    set_sensor_data(connection, plant_id, temperature, float(mean_moisture_data))
    if mean_moisture_data < Required_moisture_value:
        controller.turn_on_pump()
        mean_moisture_data_list = []
        while True:
            Moisture_data_measured, mean_moisture_data = controller.read_moisture_sensor()
            mean_moisture_data_list.append(mean_moisture_data)
            time.sleep(3)
            if mean_moisture_data >= Required_moisture_value:
                controller.turn_off_pump()
                controller.plot_pumping_readings(mean_moisture_data_list, Required_moisture_value)
                set_irrigation(connection, plant_id)
                return mean_moisture_data  # Return mean_moisture_data when irrigation is done
    else:
        print("The Moisture value is already higher than the required value, no need to pump water.")
        return mean_moisture_data  # Return mean_moisture_data even if no irrigation was needed



def get_city_by_plant_id(connection, plant_id):
    record = db_lib.get_single_result_from_query(connection, GET_CITY_QUERY, plant_id)
    if record:
        return record
    else:
        print(f"No city found for plant_ID: {plant_id}")
        return None

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

def set_sensor_data(connection, plant_id, current_temp, moisture_data_measured):
    cursor = connection.cursor()
    try:
        now = datetime.now()
        measurement_date = now.strftime('%Y-%m-%d')
        measurement_time = now.strftime('%H:%M:%S')
        data_tuple = (plant_id, measurement_date, measurement_time, current_temp, moisture_data_measured)
        cursor.execute(SET_SESNSOR_DATA_QUERY, data_tuple)
        connection.commit()
        print("Data inserted successfully into SENSOR_DATA table")
    except mysql.connector.Error as error:
        print(f"Failed to insert into MySQL table {error}")
    finally:
        cursor.close()

def set_irrigation(connection, plant_id):
    cursor = connection.cursor()
    try:
        now = datetime.now()
        irrigation_date = now.strftime('%Y-%m-%d')
        irrigation_time = now.strftime('%H:%M:%S')
        data_tuple = (plant_id, irrigation_date, irrigation_time)
        cursor.execute(SET_IRRIGATION_QUERY, data_tuple)
        connection.commit()
        print("Data inserted successfully into IRRIGATION table")
    except mysql.connector.Error as error:
        print(f"Failed to insert into MySQL table {error}")
    finally:
        cursor.close()

if __name__ == "__main__":
    plant_id = 4
    connection = db_lib.get_db_connection()

    if not connection:
        print("Failed to connect to the database.")
        exit()

    city = get_city_by_plant_id(connection, plant_id)

    if city is None:
        print("City not found for the given plant ID.")
        connection.close()
        exit()

    # Get the Required_moisture_value value from the server
    Required_moisture_value = get_required_moisture_value(connection)  # [%] Getting value from the DataBase
    if not controller.connect_to_arduino(timeout=120):
        exit()# בודק אם חיבור עובד
    if Required_moisture_value is None:
        print("Failed to get Required_moisture_value from the database.")
        connection.close()
        exit()
    while True:
        temperature = get_temp_by_city(city)
        if temperature is None:
            print("Failed to get temperature data.")
            connection.close()
            exit()

        # Get the Required_moisture_value value from the server
        Required_moisture_value = get_required_moisture_value(connection)  # [%] Getting value from the DataBase

        if Required_moisture_value is None:
            print("Failed to get Required_moisture_value from the database.")
            connection.close()
            exit()
        current_soil_moisture = pump_water_if_needed(controller, Required_moisture_value, plant_id,temperature)
        time.sleep(60)
    connection.close()
