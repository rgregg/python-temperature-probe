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
      self.log_to_console=True
      self.seconds_between_readings = 60

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

   def on_publish(self,client,userdata,rc):
      logging.info("mqtt data published")

   def on_disconnect(self, client, userdata, rc):
      logging.debug(f"mqtt on_disconnect {client}, {userdata}, {rc}")
      if rc != 0:
        logging.error("mqtt client disconnected unexpected.")
      else:
        logging.info("mqtt client disconnected")

   def run_loop(self):
      exit = self.exit;
      logging.debug(f"Exit is set: {exit.is_set()}")
      self.init_probe()
      mqttc = self.init_mqtt()
      while not exit.is_set():
         # implement main loop here
         reading = self.read_probe()
         data = reading.json()
         self.publish_topic(mqttc, self.config.topic, data)
         # sleep until next iteration of loop
         value = exit.wait(self.config.seconds_between_readings)
         logging.debug(f"event wait returned {value}")
      self.publish_topic(mqttc, self.config.status_topic, self.config.offline_status)
      mqttc.disconnect()
      mqttc.loop_stop()

   def publish_topic(self, client, topic, data):
      result = client.publish(topic, data, self.QOS1)
      if result.rc == paho.MQTT_ERR_SUCCESS:
         logging.info(f"MQTT published topic '{topic}' with '{data}'. Result: {result.rc}")
      elif result.rc == paho.MQTT_ERR_NO_CONN:
         logging.error("MQTT is not connected to a broker.")
         client.reconnect()
      else:
         logging.error(f"MQTT could not publish the message {result.rc}")

   def init_mqtt(self):
      config = self.config
      logging.info("Connecting to mqtt broker")
      mqttc = paho.Client(config.client_name)
      mqttc.on_publish = self.on_publish
      mqttc.on_disconnect = self.on_disconnect
      # Connect to broker
      mqttc.connect(config.broker,config.port)
      mqttc.loop_start()
      ret = mqttc.publish(config.status_topic, config.online_status, self.QOS1)
      # Configure LWT message for unexpected disconnect
      mqttc.will_set(config.status_topic, config.offline_status, self.QOS1)
      return mqttc

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
   logging.info(f"TempProbeReader exited gracefully.")
