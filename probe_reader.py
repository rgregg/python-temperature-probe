import board
import busio
import adafruit_si7021
import logging
from probe_reading import ProbeReading


class ProbeReader:
    def __init__(self, logger):
        self.logger = logger
        self.logger.info('Initializing data probe...')
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_si7021.SI7021(self.i2c)

    def read(self):
        if not self.sensor:
            self.logger.error('sensor has not be configured and cannot be read')
            return None
        else:
            return ProbeReading('si7021', self.sensor.temperature, self.sensor.relative_humidity)

