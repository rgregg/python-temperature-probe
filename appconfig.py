import yaml
import os.path
import logging
import json

def try_read(data, default, *args):
    try:
        current = data
        for x in args:
            current = current[x]
        logging.debug(f'read conf value {args}: {current}')
        return current
    except BaseException as err:
        logging.debug(f'error reading conf file value {args}: {err}')
    return default

class AppConfig:
    def __init__(self):
        pass

    def load_defaults(self):
        self.broker = "192.168.1.10"
        self.port = 1883
        self.topic = "house/temp-probe1/value"
        self.status_topic = "house/temp-probe1/status"
        self.client_name = "control1"
        self.offline_status = "offline"
        self.online_status = "online"
        self.log_to_console = False
        self.seconds_between_readings = 60
        self.log_path = "logs/temp-probe.log"
        self.simulate_probe = False

    def load(self):
        self.load_defaults()
        path = "temp-probe.conf"
        if os.path.exists(path):
            with open(path, "r") as yamlfile:
                data = yaml.load(yamlfile, Loader=yaml.FullLoader)
                self.client_name = try_read(data, self.client_name, 'name')
                self.broker = try_read(data, self.broker, 'mqtt', 'broker')
                self.port = try_read(data, self.port, 'mqtt', 'port')
                self.topic = try_read(data, self.topic, 'mqtt', 'value-topic')
                self.status_topic = try_read(data, self.status_topic, 'mqtt', 'status', 'topic')
                self.online_status = try_read(data, self.online_status, 'mqtt', 'status', 'online')
                self.offline_status = try_read(data, self.offline_status, 'mqtt', 'status', 'offline')
                self.log_to_console = try_read(data, self.log_to_console, 'logging', 'console')
                self.log_path = try_read(data, self.log_path, 'logging', 'path')
                self.seconds_between_readings = data['seconds-between-readings']
                self.simulate_probe = try_read(data, self.simulate_probe, 'simulate-probe')
            return True
        else:
            return False
    
    def json(self):
        return json.dumps(self.__dict__)
