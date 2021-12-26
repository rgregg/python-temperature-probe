import yaml
import os.path

class AppConfig:
    def __init__(self):
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

    def load(self):
        path = "temp-probe.conf"
        if os.path.exists(path):
            with open(path, "r") as yamlfile:
                data = yaml.load(yamlfile, Loader=yaml.FullLoader)
                self.broker = data['mqtt-broker']['address']
                self.port = data['mqtt-broker']['port']
                self.topic = data['topic']
                self.status_topic = data['status']['topic']
                self.client_name = data['name']
                self.offline_status = data['status']['offline']
                self.online_status = data['status']['online']
                self.log_to_console = data['log-to-console']
                self.seconds_between_readings = data['seconds-between-readings']
            return True
        else:
            return False
