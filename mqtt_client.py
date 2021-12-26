import paho.mqtt.client as paho
import logging

class MqttClient:
    def __init__(self, config, logger):
        self.QOS1 = 1
        self.logger = logger
        self.config = config
        self.client = self.init_mqtt()
        

    def on_publish(self,client,userdata,rc):
        self.logger.info("mqtt data published")

    def on_disconnect(self, client, userdata, rc):
        self.logger.debug(f"mqtt on_disconnect {client}, {userdata}, {rc}")
        if rc != 0:
            self.logger.error("mqtt client disconnected unexpected.")
        else:
            self.logger.info("mqtt client disconnected")

    def publish_topic(self, topic, data, retain):
        result = self.client.publish(topic, data, self.QOS1, retain)
        if result.rc == paho.MQTT_ERR_SUCCESS:
            self.logger.info(f"MQTT published topic '{topic}' with '{data}'. Result: {result.rc}")
        elif result.rc == paho.MQTT_ERR_NO_CONN:
            self.logger.error("MQTT is not connected to a broker.")
            self.client.reconnect()
        else:
            self.logger.error(f"MQTT could not publish the message {result.rc}")
    
    def disconnect(self):
        self.client.disconnect()
        self.client.loop_stop()


    def init_mqtt(self):
        self.logger.info("Connecting to mqtt broker")
        mqttc = paho.Client(self.config.client_name)
        mqttc.on_publish = self.on_publish
        mqttc.on_disconnect = self.on_disconnect
        # Connect to broker
        mqttc.connect(self.config.broker,self.config.port)
        mqttc.loop_start()
        ret = mqttc.publish(self.config.status_topic, self.config.online_status, self.QOS1, True)
        # Configure LWT message for unexpected disconnect
        mqttc.will_set(self.config.status_topic, self.config.offline_status, self.QOS1, True)
        return mqttc
