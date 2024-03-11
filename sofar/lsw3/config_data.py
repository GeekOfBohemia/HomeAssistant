import os
import sys
from dataclasses import dataclass
import configparser


@dataclass
class ConfigData:
    inverter_ip: str
    inverter_port: int
    inverter_sn: int
    mqtt_basic: str
    mqtt_server: str
    mqtt_port: int
    mqtt_topic: str
    mqtt_username: str
    ha_mqtt_topic: str

    def __init__(self):
        configParser = configparser.RawConfigParser()
        data_file_path = os.path.join(os.path.dirname(__file__), "config.cfg")
        configParser.read(data_file_path)

        self.inverter_ip = configParser.get("SofarInverter", "inverter_ip")
        self.inverter_port = int(configParser.get("SofarInverter", "inverter_port"))
        self.inverter_sn = int(configParser.get("SofarInverter", "inverter_sn"))
        self.mqtt_server = configParser.get("MQTT", "mqtt_server")
        self.mqtt_port = int(configParser.get("MQTT", "mqtt_port"))
        self.mqtt_username = configParser.get("MQTT", "mqtt_username")
        self.mqtt_passwd = configParser.get("MQTT", "mqtt_passwd")
        self.ha_mqtt_topic = configParser.get("HomeAssistant", "ha_mqtt_topic")


configData: ConfigData = ConfigData()
