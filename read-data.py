import datetime
import time
import board
import busio
import adafruit_si7021
import os
from google.cloud import pubsub_v1
import json
from time import gmtime, strftime
import logging

logging.basicConfig(filename='temp-probe.log',level=logging.DEBUG)

time_between_readings_seconds = 60
logging.info('Initializing data probe...')
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_si7021.SI7021(i2c)

logging.info('Initializing Google Cloud Library...')
publisher = pubsub_v1.PublisherClient.from_service_account_json('gcp_keys.json')
topic_path = publisher.topic_path('gregg-temperature-recorder', 'basement-data')

futures = dict()

class ProbeReading:
    def __init__(self, device, temperature, humidity):
        self.device = device
        self.temp_c = temperature
        self.temp_f = 32 + (temperature * 9 / 5)
        self.relative_humidity = humidity
        self.date_time_utc = datetime.datetime.utcnow().isoformat()

def get_callback(f, data):
    def callback(f):
        try:
           futures.pop(data)
        except: #noqa
           logging.error('Please handle {} for {}.'.format(f.exception(), data))
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

    logging.info("Temperature: %0.1f C" % next_reading.temp_c)
    logging.info("Humidity: %0.1f %%" % next_reading.relative_humidity)
    logging.info("Date/Time: %s" % next_reading.date_time_utc)
    logging.info("Sensor: %s" % next_reading.device)
    time.sleep(time_between_readings_seconds)


