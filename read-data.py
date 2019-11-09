import datetime
import time
import board
import busio
import adafruit_si7021
import os
from google.cloud import pubsub_v1
import json
from time import gmtime, strftime


time_between_readings_seconds = 60
print('Initializing data probe...')
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_si7021.SI7021(i2c)

print('Initializing Google Cloud Library...')
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path('gregg-temperature-recorder', 'basement-data')

futures = dict()

class ProbeReading:
    def __init__(self, device, temperature, humidity):
        self.device_id = device
        self.temp_c = temperature
        self.temp_f = 32 + (temperature * 9 / 5)
        self.relative_humidity = humidity
        self.date_time_utc = datetime.datetime.utcnow().isoformat()

def get_callback(f, data):
    def callback(f):
        try:
           print(f.result())
           futures.pop(data)
        except: #noqa
           print('Please handle {} for {}.'.format(f.exception(), data))
    return callback

while True:
    next_reading = ProbeReading('si7021', sensor.temperature, sensor.relative_humidity)
    data = json.dumps(next_reading.__dict__)
    futures.update({data: None})

    # When you publish a message, the client returns a future.
    future = publisher.publish(
        topic_path, data=data.encode('utf-8')  # data must be a bytestring
    )
    futures[data] = future
    # Publish failures shall be handled in the callback function.
    future.add_done_callback(get_callback(future, data))

    print("\nTemperature: %0.1f C" % next_reading.temp_c)
    print("Temperature: %0.1f F" % next_reading.temp_f)
    print("Humidity: %0.1f %%" % next_reading.relative_humidity)
    print("Date/Time: %s" % next_reading.date_time_utc)
    print("Sensor: %s" % next_reading.device_id)
    print('Sleeping {} seconds', time_between_readings_seconds)
    time.sleep(time_between_readings_seconds)


