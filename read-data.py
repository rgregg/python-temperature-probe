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
from threading import Event

class ProbeConfig:
   def __init__(self):
      self.broker="192.168.42.65"
      self.port=1883
      self.topic="house/temp-probe1"
      self.status_topic="house/temp-probe1/status"
      self.client_name="control1"
      self.offline_status="offline"
      self.online_status="online"
      self.log_to_console=False
      self.seconds_between_readings = 60

class GracefulKiller:
  kill_now = False
  def __init__(self):


class ProbeReading:
   def __init__(self, device, temperature, humidity):
        self.device = device
        self.temp_c = temperature
        self.temp_f = 32 + (temperature * 9 / 5)
        self.relative_humidity = humidity
        self.date_time_utc = datetime.datetime.utcnow().isoformat()
   def json(self):
      return json.dumps(self.__dict__)

class TempProbeReader:
   def __init__(self, config):
      self.exit = Event()
      self.config = config
      self.killer = GracefulKiller()
      self.QOS1 = 1
      self.sensor = None
      logging.basicConfig(filename='temp-probe.log',level=logging.DEBUG)
      if config.log_to_console == True:
         logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
      signal.signal(signal.SIGINT, self.exit_gracefully)
      signal.signal(signal.SIGTERM, self.exit_gracefully)

   def exit_gracefully(self, *args):
      logging.info(f"Interrupted by {args}")
      self.exit.set();

   def on_publish(client,userdata,rc):
      logging.info("mqtt data published")

   def on_disconnect(client, userdata, rc):
      logging.info("mqtt client disconnected")

   def run_loop(self):
      exit = self.exit;
      self.init_probe()
      self.init_mqtt()
      while not exit.is_set:
         # implement main loop here
         reading = self.read_probe()
         data = reading.json()
         self.publish_topic(self.config.topic, data)
         # sleep until next iteration of loop
         exit.wait(self.config.seconds_between_readings)

   def publish_topic(self, topic, data):
      result = self.client.publish(topic, data, self.QOS1)
      logging.info(f"MQTT published. Result: {result.rc}")

   def init_mqtt(self):
      config = self.config
      logging.info("Connecting to mqtt broker")
      client1 = paho.Client(config.client_name)
      client1.on_publish = self.on_publish
      client1.on_disconnect = self.on_disconnect
      # Configure LWT message for unexpected disconnect
      client1.will_set(config.status_topic, config.offline_status, self.QOS1, retain=False)
      # Connect to broker
      client1.connect(config.broker,config.port)
      ret = client1.publish(config.status_topic, config.online_status, self.QOS1)

   def init_probe(self):
      logging.info('Initializing data probe...')
      self.i2c = busio.I2C(board.SCL, board.SDA)
      self.sensor = adafruit_si7021.SI7021(self.i2c)

   def read_probe(self):
      if not self.sensor:
         logging.error('sensor has not be configured and cannot be read')
      else:
         next_reading = ProbeReading('si7021', self.sensor.temperature, self.sensor.relative_humidity)
         logging.info(f"{next_reading.date_time_utc} - temp {next_reading.temp_c:.1f} C / {next_reading.temp_f:.1f} F" \
                      f" - humidity {next_reading.relative_humidity:.1f} %")
         return next_reading


if __name__ == '__main__':
   config = ProbeConfig()
   reader = TempProbeReader(config)
   reader.run_loop()
   logging.info(f"completed gracefully.")