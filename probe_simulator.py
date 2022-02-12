import logging
from probe_reading import ProbeReading


class ProbeSimulator:
    def __init__(self, logger):
        logger.info('Initializing simulated data probe.')

    def read(self):
        return ProbeReading('si7021', 19.1, 49.1)

