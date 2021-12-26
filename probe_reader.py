import datetime
import json
import board
import busio
import adafruit_si7021
import logging
from time import gmtime, strftime


class ProbeReading:
    def __init__(self, device, temperature, humidity):
        self.device = device
        self.temp_c = temperature
        self.temp_f = 32 + (temperature * 9 / 5)
        self.relative_humidity = humidity
        self.date_time_utc = datetime.datetime.utcnow().isoformat()
    
    def json(self):
      return json.dumps(self.__dict__)

class ProbeReader:
    def init_probe(self, logger):
        self.logger = logger
        self.logger.info('Initializing data probe...')
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_si7021.SI7021(self.i2c)

    def read(self):
        if not self.sensor:
            self.logger.error('sensor has not be configured and cannot be read')
            return None
        else:
            next_reading = ProbeReading('si7021', self.sensor.temperature, self.sensor.relative_humidity)
            self.logger.info(f"{next_reading.date_time_utc} - temp {next_reading.temp_c:.1f} C / {next_reading.temp_f:.1f} F" \
                             f" - humidity {next_reading.relative_humidity:.1f} %")
        return next_reading

