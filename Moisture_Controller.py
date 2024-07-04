import time
import serial
import numpy as np
import matplotlib.pyplot as plt

class MoistureController:
    def __init__(self, serial_port, baud_rate, min_reading, max_reading, num_samples, std_threshold):
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.min_reading = min_reading
        self.max_reading = max_reading
        self.num_samples = num_samples
        self.std_threshold = std_threshold
        self.ser = None


    def connect_to_arduino(self, timeout=15):
        start_time = time.time()
        while True:
            try:
                self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
                time.sleep(4)
                
                # Read the initialization message from Arduino
                message = self.ser.readline().decode().strip()
                print("Arduino message:", message)
                
                # Print connection confirmation
                print("Connected to Arduino successfully!")
                return True
            
            except serial.SerialException as e:
                # Print error message if connection fails
                print("Failed to connect to Arduino:", e)
                if time.time() - start_time >= timeout:
                    print("Connection timeout reached")
                    return False
                time.sleep(1)

    def read_moisture_sensor(self):
        while True:
            self.ser.write(b'S') #לקרוא את החיישן
            time.sleep(1)
            line = self.ser.readline().decode().strip()
            time.sleep(2)
            self.ser.flush()
            if line:
                readings = line.split(',')
                readings = np.array(readings[:-1], dtype=int)
                readings_in_percentages = 100 - 100 * (readings - self.min_reading) / (self.max_reading - self.min_reading) #נרמול מביתים לאחוזים
                std_readings = np.std(readings_in_percentages)
                
                # check if the readings are stable
                if std_readings > self.std_threshold:
                    print("The sensor is not stable. Invalid readings, retrying...")
                    return self.read_moisture_sensor()
                else:
                    readings_mean_in_percentages = np.mean(readings_in_percentages)
                    print("#### Sensor Readings ####")
                    print(f"Sensor readings mean: {readings_mean_in_percentages:.2f} %")
                    print(f"Sensor readings std: {std_readings:.2f} %")
                    print("Sensor Raw Data:")
                    print(", ".join([f"{reading:.2f} %" for reading in readings_in_percentages]))
                    print('---------------------------------------')
                    return readings_in_percentages, readings_mean_in_percentages

    def turn_on_pump(self):
        self.ser.write(b'O')
        print(self.ser.readline().decode().strip())
        self.ser.flush()
        time.sleep(2)
        print("Pumping water...")

    def turn_off_pump(self):
        self.ser.write(b'F')
        print(self.ser.readline().decode().strip())
        self.ser.flush()
        time.sleep(2)

    def plot_readings(self, Moisture_data_measured, mean_moisture_data, Required_moisture_value):

        fig = plt.figure(figsize=(8, 5))
        plt.plot(Moisture_data_measured, label='Sensor Readings', marker='o')
        plt.axhline(y=Required_moisture_value, color='r', linestyle='--', label='Required Moisture Value')
        plt.axhline(y=mean_moisture_data, color='g', linestyle='--', label='Mean Moisture Readings')
        plt.xlabel('Sample Index')
        plt.ylabel('Moisture Value [%]')
        plt.title('Moisture Sensor Readings')
        plt.legend()
        plt.pause(4)
        plt.close(fig)

    def plot_pumping_readings(self, mean_moisture_data_list, Required_moisture_value):
        fig = plt.figure(figsize=(8, 5))
        plt.axhline(y=Required_moisture_value, color='r', linestyle='--', label='Required Moisture Value')
        plt.plot(mean_moisture_data_list, label='Mean Moisture Readings', marker='o')
        plt.xlabel('Sample index')
        plt.ylabel('Moisture Value [%]')
        plt.title('Mean Moisture Readings during Pumping Water')
        plt.legend()

        plt.pause(4)
        plt.close(fig)