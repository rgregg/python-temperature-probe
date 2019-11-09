import time
import board
import busio
import adafruit_si7021
import os
#from google.cloud import pubsub_v1
import json
from time import gmtime, strftime

i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_si7021.SI7021(i2c)
#publisher = pubsub_v1.PublisherClient()
topic_name = 'projects/gregg-temperature-recorder/topics/basement-data'

class ProbeReading:

    def __init__(self, device, temperature, humidity):
        self.device_id = 'si7021'
        self.temp_c = temperature
        self.temp_f = 32 + (temperature * 9 / 5)
        self.relative_humidity = humidity
        self.date_time_utc = strftime("%Y-%m-%dT%H:%M:%S%z", gmtime())


while True:
    next_reading = ProbeReading('si7021', sensor.temperature, sensor.relative_humidity)

    print("\nTemperature: %0.1f C" % next_reading.temp_c)
    print("Temperature: %0.1f F" % next_reading.temp_f)
    print("Humidity: %0.1f %%" % next_reading.relative_humidity)
    print("Date/Time: %s" % next_reading.date_time_utc)
    print("Sensor: %s" % next_reading.device_id)
    time.sleep(2)


