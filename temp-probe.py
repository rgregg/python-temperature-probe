import sys
import logging
from logging.handlers import TimedRotatingFileHandler
import signal
from threading import Event
import config
import mqtt_client
import probe_reader

class ProbeReporterApp:
   def __init__(self, config):
      self.logger = self.enable_logging()
      self.exit = Event()
      self.mqttc = mqtt_client.MqttClient(config, self.logger)
      self.config = config
      
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

   def run_loop(self):
      config = self.config;
      exit = self.exit;
      probe = ProbeReader(self.logger)
      
      while not exit.is_set():
         reading = probe.read()
         data = reading.json()
         self.mqttc.publish_topic(config.topic, data, False)
         exit.wait(config.seconds_between_readings)

      self.mqttc.publish_topic(config.status_topic, config.offline_status, True)
      self.mqttc.disconnect()

if __name__ == '__main__':
   config = AppConfig()
   config.load()
   reader = ProbeReporterApp(config)
   reader.run_loop()
   reader.logger.info(f"ProbeReporterApp exited gracefully.")




