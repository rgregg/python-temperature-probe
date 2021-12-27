import sys
import logging
from logging.handlers import TimedRotatingFileHandler
import signal
from threading import Event
from appconfig import AppConfig
from mqtt_client import MqttClient
import dimport

class ProbeReporterApp:
   def __init__(self, config):
      self.config = config
      self.logger = self.enable_logging()
      self.exit = Event()
      self.mqttc = MqttClient(config, self.logger)
      
      signal.signal(signal.SIGINT, self.exit_gracefully)
      signal.signal(signal.SIGTERM, self.exit_gracefully)

   def enable_logging(self):
      logger = logging.getLogger('probe-reporter')
      logger.setLevel(logging.INFO)
      handler = TimedRotatingFileHandler(self.config.log_path,
                                    when='d',
                                    interval=1,
                                    backupCount=7)
      logger.addHandler(handler)
      if appconfig.log_to_console:
         logger.addHandler(logging.StreamHandler(sys.stdout))
      return logger

   def exit_gracefully(self, *args):
      self.logger.info(f"Interrupted by {args}")
      self.exit.set()

   def run_loop(self):
      config = self.config
      exit = self.exit

      probe = None
      if self.config.simulate_probe:
         probe = dimport.dynload("probe_simulator", "ProbeSimulator", self.logger)
      else:
         probe = dimport.dynload("probe_reader", "ProbeReader", self.logger)

      while not exit.is_set():
         reading = probe.read()
         self.logger.info(f"{reading.date_time_utc} - temp {reading.temp_c:.1f} C / {reading.temp_f:.1f} F" \
                          f" - humidity {reading.relative_humidity:.1f} %")

         data = reading.json()
         self.mqttc.publish_topic(config.topic, data, False)
         exit.wait(config.seconds_between_readings)

      self.mqttc.publish_topic(config.status_topic, config.offline_status, True)
      self.mqttc.disconnect()

if __name__ == '__main__':
   appconfig = AppConfig()
   appconfig.load()
   print(appconfig.json())

   reader = ProbeReporterApp(appconfig)
   reader.run_loop()
   reader.logger.info(f"ProbeReporterApp exited gracefully.")




