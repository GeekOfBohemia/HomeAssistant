# <discovery_prefix>/<component>/[<node_id>/]<object_id>/config
# - ciste
#  homeassistant/sensor/SofarLogger/config {"name": "Frequency_Grid", "device_class": "frequency", "unit_of_measurement": "Hz","state_topic": "homeassistant/sensor/SofarLogger/Frequency_Grid/state"}'
#  homeassistant/sensor/SofarLogger/Frequency_Grid/state
#  55
# - node
#  homeassistant/sensor/SofarLogger_2380228322_1156/Frequency_Grid/config {"name": "Frequency_Grid", "device_class": "frequency", "unit_of_measurement": "Hz","state_topic": "homeassistant/sensor/SofarLogger_2380228322_1156/Frequency_Grid/state"}
#  homeassistant/sensor/SofarLogger_2380228322_1156/Frequency_Grid/state
#  55
#  homeassistant/sensor/SofarLogger_2380228322_1157/ActivePower_Output_Total/config
# {"name": "ActivePower_Output_Total", "device_class": "Power", "unit_of_measurement": "kW", "state_topic": "homeassistant/sensor/SofarLogger_2380228322_1157/ActivePower_Output_Total/state"}
#
# homeassistant/sensor/SofarLogger_2380228322_1157/ActivePower_Output_Total/state
# 150
#  homeassistant/SofarLogger/sensor/2380228322_1156/Frequency_grid/config
# {"name": "Frequency_grid", "device_class": "Power", "unit_of_measurement": "kW", "state_topic": "homeassistant/sensor/SofarLogger/2380228322_1156/ActivePower_Output_Total/state"}
#
# homeassistant/sensor/SofarLogger/2380228322_1156/ActivePower_Output_Total/state
# 150


import json
import paho.mqtt.client as paho
import os
import sys
from appframe.logger import app_log

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from appframe.config_data import configData

TOPIC = "homeassistant/sensor/"
MQTT_SENSOR_NAME = "name"
MQTT_SENSOR_DEVICE_NAME = "device_name"
MQTT_SENSOR_DEVICE_CLASS = "device_class"
MQTT_SENSOR_DEVICE_IDENTIFIER = "identifier"
MQTT_SENSOR_UNIT = "unit_of_measurement"
MQTT_SENSOR_STATE_TOPIC = "state_topic"
MQTT_SENSOR_UNIQUE_ID = "unique_id"
MQTT_SENSOR_ID = "sensor_id"
MQTT_SENSOR_PREFIX_ID = "sensor_prefix_id"
MQTT_SENSOR_STATE = "state"


class HomeAssistantMQTT:
    def __init__(self):
        self.client = paho.Client("inverter")
        self.client.username_pw_set(
            username=configData.mqtt_username, password=configData.mqtt_passwd
        )
        self.connected = False
        self.connect()

    def __del__(self):
        try:
            if self.connected:
                self.client.disconnect()
        except:
            pass

    def connect(self) -> bool:
        if self.connected:
            return True
        self.connected = True
        # print(f"Server: {configData.mqtt_server} port: {configData.mqtt_port}")
        try:
            self.client.connect(configData.mqtt_server, configData.mqtt_port)
            self.client.loop_start()
        except:
            self.connected = False
        return self.connected

    def publish(self, topic, data):
        if not self.connect():
            return
        result = self.client.publish(topic, data)
        try:
            result.wait_for_publish()
        except:
            print("Error publishing data to MQTT")
        if result.is_published:
            app_log.info("*** Data has been succesfully published to MQTT ")
        else:
            print("Error publishing data to MQTT")

    def discover_sensor(self, mqtt_data):
        #  homeassistant/sensor/SofarLogger_2380228322_1157/ActivePower_Output_Total/config
        # homeassistant/sensor/identifier/name/config

        mqtt_data[MQTT_SENSOR_STATE_TOPIC] = (
            mqtt_data.get(MQTT_SENSOR_DEVICE_NAME, "").lower()
            + "/"
            + mqtt_data.get(MQTT_SENSOR_ID, "")
        )
        mqtt_data[MQTT_SENSOR_UNIQUE_ID] = (
            mqtt_data.get(MQTT_SENSOR_PREFIX_ID, "")
            + "_"
            + mqtt_data.get(MQTT_SENSOR_ID, "")
        )

        identifier = mqtt_data.get(MQTT_SENSOR_ID, "")
        topic = TOPIC + identifier + "/config"
        state_topic = mqtt_data.get(MQTT_SENSOR_STATE_TOPIC, "")

        data_json = {
            MQTT_SENSOR_NAME: mqtt_data.get("name", ""),
            MQTT_SENSOR_DEVICE_CLASS: mqtt_data.get("device_class", ""),
            MQTT_SENSOR_UNIT: mqtt_data.get("unit_of_measurement", ""),
            MQTT_SENSOR_STATE_TOPIC: state_topic,
            MQTT_SENSOR_UNIQUE_ID: mqtt_data.get("unique_id", ""),
            "device": {
                "name": mqtt_data.get(MQTT_SENSOR_DEVICE_NAME, ""),
                "identifiers": [mqtt_data.get(MQTT_SENSOR_DEVICE_IDENTIFIER, "")],
            },
        }

        self.publish(topic, json.dumps(data_json))
        self.publish(state_topic, mqtt_data.get(MQTT_SENSOR_STATE, ""))
