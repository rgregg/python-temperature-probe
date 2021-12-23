import sys
import datetime
import time
import board
import busio
import adafruit_si7021
import os
import json
from time import gmtime, strftime
import logging
import paho.mqtt.client as paho
import signal

#enable logging
logging.basicConfig(filename='temp-probe.log',level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

class ProbeConfig:
   def __init__(self):
      self.broker="192.168.42.65"
      self.port=1883
      self.topic="house/temp-probe1"
      self.status_topic="house/temp-probe1/status"
      self.client_name="control1"
      self.offline_status="offline"
      self.online_status="online"

class GracefulKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self, *args):
    self.kill_now = True

if __name__ == '__main__':
   killer = GracefulKiller()
   while not killer.kill_now:
      

config=ProbeConfig()
QOS1=1




def on_publish(client,userdata,rc):
   logging.info("mqtt data published")

def on_disconnect(client, userdata, rc):
   logging.info("mqtt client disconnected");


# Configure the client
logging.info("connecting to mqtt broker")
client1 = paho.Client(config.client_name)
client1.on_publish = on_publish
client1.on_disconnect = on_disconnect
# Configure LWT message for unexpected disconnect
client1.will_set(config.status_topic, config.offline_status, QOS1, retain=False)
# Connect to broker
client1.connect(config.broker,config.port)
ret = client1.publish(config.status_topic, config.online_status, QOS1)


time_between_readings_seconds = 60
logging.info('Initializing data probe...')
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_si7021.SI7021(i2c)

class ProbeReading:
    def __init__(self, device, temperature, humidity):
        self.device = device
        self.temp_c = temperature
        self.temp_f = 32 + (temperature * 9 / 5)
        self.relative_humidity = humidity
        self.date_time_utc = datetime.datetime.utcnow().isoformat()

# Main loop for reading temperature data
while True:
    next_reading = ProbeReading('si7021', sensor.temperature, sensor.relative_humidity)
    data = json.dumps(next_reading.__dict__)

    logging.info(f"{next_reading.date_time_utc} - temp {next_reading.temp_c:.1f} C / {next_reading.temp_f:.1f} F" \
                 f" - humidity {next_reading.relative_humidity:.1f} %")

#    logging.info("Temperature: %0.1f C / %0.1f F" % (next_reading.temp_c, next_reading.temp_f))
#    logging.info("Humidity: %0.1f %%" % next_reading.relative_humidity)
#    logging.info("Date/Time: %s" % next_reading.date_time_utc)
#    logging.info("Sensor: %s" % next_reading.device)

    ret = client1.publish(config.topic, data, QOS1)
    logging.info(f"mqtt publish result {ret.rc}")

    time.sleep(time_between_readings_seconds)


