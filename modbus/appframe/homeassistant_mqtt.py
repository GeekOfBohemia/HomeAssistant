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
MQTT_SENSOR_ICON = "icon"


class HomeAssistantMQTT:
    mqtt_def_topics = []

    def __init__(self, client_name: str):
        self.client = paho.Client(client_name)
        err: str = "V souboru config.cfg v oddile [MQTT] musi byt uvedeno:"
        hassError: bool = False
        for el in ("mqtt_username", "mqtt_passwd", "mqtt_server", "mqtt_port"):
            if not hasattr(configData, el):
                hassError = True
                err += "\n - " + el
        if hassError:
            app_log.error(err)
            sys.exit()
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

    def publish(self, topic, data) -> bool:
        retval: bool = False
        if not self.connect():
            return False
        result = self.client.publish(topic, data)
        try:
            result.wait_for_publish()
        except:
            pass
            # print("Error publishing data to MQTT")
        try:
            if result.is_published:
                retval = True
                app_log.info("*** Data has been succesfully published to MQTT ")
            else:
                pass
                # Zde nema cenu vypisovat error - casty pripad
        except:
            pass
        return retval

    def discover_sensor(self, mqtt_data, debug: bool = False):
        # MQTT_SENSOR_DEVICE_NAME - device_name
        #
        # MQTT_SENSOR_PREFIX_ID - sensor_prefix_id
        # MQTT_SENSOR_ID - sensor_id
        # - unit_of_measurement
        # - device_class
        # - unique_id
        # MQTT_SENSOR_DEVICE_IDENTIFIER - identifier

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
        m_topic: str = "homeassistant/sensor/"
        identifier = mqtt_data.get(MQTT_SENSOR_ID, "")
        topic = m_topic + identifier + "/config"
        state_topic = mqtt_data.get(MQTT_SENSOR_STATE_TOPIC, "")
        unit_of_measurement = mqtt_data.get("unit_of_measurement", "")

        data_json = {
            MQTT_SENSOR_NAME: mqtt_data.get("name", ""),
            MQTT_SENSOR_DEVICE_CLASS: mqtt_data.get("device_class", ""),
            MQTT_SENSOR_STATE_TOPIC: state_topic,
            MQTT_SENSOR_UNIQUE_ID: mqtt_data.get("unique_id", ""),
            "device": {
                "name": mqtt_data.get(MQTT_SENSOR_DEVICE_NAME, ""),
                "identifiers": [mqtt_data.get(MQTT_SENSOR_DEVICE_IDENTIFIER, "")],
            },
        }
        if unit_of_measurement:
            data_json[MQTT_SENSOR_UNIT] = unit_of_measurement

        if not topic in HomeAssistantMQTT.mqtt_def_topics:
            if debug:
                app_log.debug(">>>> Define")
                app_log.debug(f"topic: {topic}")
                app_log.debug(data_json)
            if self.publish(topic, json.dumps(data_json)):
                HomeAssistantMQTT.mqtt_def_topics.append(topic)
        state = mqtt_data.get(MQTT_SENSOR_STATE, "")
        if debug:
            app_log.debug(f"state_topic: {state_topic} state: {state}")

        self.publish(state_topic, state)

    def discover_binary_sensor(self, mqtt_data, debug: bool = False):
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
        m_topic: str = "homeassistant/binary_sensor/"

        identifier = mqtt_data.get(MQTT_SENSOR_ID, "")
        topic = m_topic + identifier + "/config"
        state_topic = mqtt_data.get(MQTT_SENSOR_STATE_TOPIC, "")
        unit_of_measurement = mqtt_data.get("unit_of_measurement", "")

        # Nutno dopracovat
        data_json = {
            MQTT_SENSOR_NAME: mqtt_data.get("name", ""),
            MQTT_SENSOR_DEVICE_CLASS: mqtt_data.get("device_class", ""),
            MQTT_SENSOR_STATE_TOPIC: state_topic,
            MQTT_SENSOR_UNIQUE_ID: mqtt_data.get("unique_id", ""),
            MQTT_SENSOR_ICON: mqtt_data.get("icon", ""),
            "device": {
                "name": mqtt_data.get(MQTT_SENSOR_DEVICE_NAME, ""),
                "identifiers": [mqtt_data.get(MQTT_SENSOR_DEVICE_IDENTIFIER, "")],
            },
        }
        if unit_of_measurement:
            data_json[MQTT_SENSOR_UNIT] = unit_of_measurement

        if not topic in HomeAssistantMQTT.mqtt_def_topics:
            if debug:
                app_log.debug(">>>> Define")
                app_log.debug(f"topic: {topic}")
                app_log.debug(data_json)
            self.publish(topic, json.dumps(data_json))
            HomeAssistantMQTT.mqtt_def_topics.append(topic)
        state = mqtt_data.get(MQTT_SENSOR_STATE, "")
        if debug:
            app_log.debug("----")
            app_log.debug(f"state_topic: {state_topic} state: {state}")

        self.publish(state_topic, state)
