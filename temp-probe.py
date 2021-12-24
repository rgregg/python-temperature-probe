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
from logging.handlers import TimedRotatingFileHandler
import paho.mqtt.client as paho
import signal
from threading import Event

class ProbeConfig:
   def __init__(self, raw = None):
      if raw is None:
         self.broker="192.168.42.65"
         self.port=1883
         self.topic="house/temp-probe1/value"
         self.status_topic="house/temp-probe1/status"
         self.client_name="control1"
         self.offline_status="offline"
         self.online_status="online"
         self.log_to_console=False
         self.seconds_between_readings = 60
         self.log_path = "/home/pi/temp-probe-python/logs/temp-probe.log"
      else:
         self.broker = raw['mqtt-broker']['address']
         self.port = raw['mqtt-broker']['port']
         self.topic = raw['topic']
         self.status_topic = raw['status']['topic']
         self.client_name = raw['name']
         self.offline_status = raw['status']['offline']
         self.online_status = raw['status']['online']
         self.log_to_console = raw['log-to-console']
         self.seconds_between_readings = raw['seconds-between-readings']

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
      self.logger = self.enable_logging()
      signal.signal(signal.SIGINT, self.exit_gracefully)
      signal.signal(signal.SIGTERM, self.exit_gracefully)

   def enable_logging(self):
      logger = logging.getLogger('rotating logs')
      logger.setLevel(logging.INFO)

      handler = TimedRotatingFileHandler(self.config.log_path,
                                    when='d',
                                    interval=1,
                                    backupCount=7)
      logger.addHandler(handler)
      if config.log_to_console:
         logger.addHandler(logging.StreamHandler(sys.stdout))
      return logger

   def exit_gracefully(self, *args):
      self.logger.info(f"Interrupted by {args}")
      self.exit.set();

   def on_publish(self,client,userdata,rc):
      self.logger.info("mqtt data published")

   def on_disconnect(self, client, userdata, rc):
      self.logger.debug(f"mqtt on_disconnect {client}, {userdata}, {rc}")
      if rc != 0:
        self.logger.error("mqtt client disconnected unexpected.")
      else:
        self.logger.info("mqtt client disconnected")

   def run_loop(self):
      exit = self.exit;
      self.logger.debug(f"Exit is set: {exit.is_set()}")
      self.init_probe()
      mqttc = self.init_mqtt()
      while not exit.is_set():
         # implement main loop here
         reading = self.read_probe()
         data = reading.json()
         self.publish_topic(mqttc, self.config.topic, data, False)
         # sleep until next iteration of loop
         value = exit.wait(self.config.seconds_between_readings)
         self.logger.debug(f"event wait returned {value}")
      self.publish_topic(mqttc, self.config.status_topic, self.config.offline_status, True)
      mqttc.disconnect()
      mqttc.loop_stop()

   def publish_topic(self, client, topic, data, retain):
      result = client.publish(topic, data, self.QOS1, retain)
      if result.rc == paho.MQTT_ERR_SUCCESS:
         self.logger.info(f"MQTT published topic '{topic}' with '{data}'. Result: {result.rc}")
      elif result.rc == paho.MQTT_ERR_NO_CONN:
         self.logger.error("MQTT is not connected to a broker.")
         client.reconnect()
      else:
         self.logger.error(f"MQTT could not publish the message {result.rc}")

   def init_mqtt(self):
      config = self.config
      self.logger.info("Connecting to mqtt broker")
      mqttc = paho.Client(config.client_name)
      mqttc.on_publish = self.on_publish
      mqttc.on_disconnect = self.on_disconnect
      # Connect to broker
      mqttc.connect(config.broker,config.port)
      mqttc.loop_start()
      ret = mqttc.publish(config.status_topic, config.online_status, self.QOS1, True)
      # Configure LWT message for unexpected disconnect
      mqttc.will_set(config.status_topic, config.offline_status, self.QOS1, True)
      return mqttc

   def init_probe(self):
      self.logger.info('Initializing data probe...')
      self.i2c = busio.I2C(board.SCL, board.SDA)
      self.sensor = adafruit_si7021.SI7021(self.i2c)

   def read_probe(self):
      if not self.sensor:
         self.logger.error('sensor has not be configured and cannot be read')
      else:
         next_reading = ProbeReading('si7021', self.sensor.temperature, self.sensor.relative_humidity)
         self.logger.info(f"{next_reading.date_time_utc} - temp {next_reading.temp_c:.1f} C / {next_reading.temp_f:.1f} F" \
                      f" - humidity {next_reading.relative_humidity:.1f} %")
         return next_reading


if __name__ == '__main__':
   config = ProbeConfig()
   reader = TempProbeReader(config)
   reader.run_loop()
   reader.logger.info(f"TempProbeReader exited gracefully.")




