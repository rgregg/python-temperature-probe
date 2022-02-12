import datetime
import json

class ProbeReading:
    def __init__(self, device, temperature_c, humidity):
        self.device = device
        self.temp_c = temperature_c
        self.temp_f = 32 + (temperature_c * 9 / 5)
        self.relative_humidity = humidity
        self.date_time_utc = datetime.datetime.utcnow().isoformat()
    
    def json(self):
      return json.dumps(self.__dict__)

