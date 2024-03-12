import os
import sys
from dataclasses import dataclass
import configparser

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from appframe.helpers import HelperOp


@dataclass
class ConfigData:
    inverter_ip: str
    inverter_port: int
    inverter_sn: int
    mqtt_server: str
    mqtt_port: int
    mqtt_username: str

    def __init__(self):
        configParser = configparser.RawConfigParser()
        data_file_path = HelperOp.filename("config.cfg")
        configParser.read(data_file_path)

        try:
            self.inverter_ip = configParser.get("SofarInverter", "inverter_ip")
            self.inverter_port = int(configParser.get("SofarInverter", "inverter_port"))
            self.inverter_sn = int(configParser.get("SofarInverter", "inverter_sn"))
        except:
            pass
        try:
            self.mqtt_server = configParser.get("MQTT", "mqtt_server")
            self.mqtt_port = int(configParser.get("MQTT", "mqtt_port"))
            self.mqtt_username = configParser.get("MQTT", "mqtt_username")
            self.mqtt_passwd = configParser.get("MQTT", "mqtt_passwd")
        except:
            pass
        try:
            self.ha_ip = configParser.get("HomeAssistant", "ip")
            self.ha_port = configParser.get("HomeAssistant", "port")
            self.ha_url = f"http://{self.ha_ip}:{self.ha_port}/"
            # self.ha_url = f"https://{self.ha_ip}:{self.ha_port}/"
            self.ha_api_authorization = configParser.get(
                "HomeAssistant", "api_authorization"
            )
            self.app_framework = configParser.get("HomeAssistant", "app_framework")
        except:
            pass


configData: ConfigData = ConfigData()
if __name__ == "__main__":
    print(configData.ha_url)
    print(configData.ha_api_authorization)
