import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lsw3.globals import (
    REG_ADDR,
    REG_DEVICE_CLASS,
    REG_FRIENDLY_NAME,
    REG_ID,
    REG_RATIO,
    REG_TITLE,
    REG_TYPE,
    REG_UNIT,
    REG_VALUE,
)
from appframe.homeassistant_mqtt import (
    MQTT_SENSOR_DEVICE_CLASS,
    MQTT_SENSOR_DEVICE_IDENTIFIER,
    MQTT_SENSOR_DEVICE_NAME,
    MQTT_SENSOR_ID,
    MQTT_SENSOR_NAME,
    MQTT_SENSOR_PREFIX_ID,
    MQTT_SENSOR_STATE,
    MQTT_SENSOR_UNIT,
    HomeAssistantMQTT,
)


DEVICE_NAME = "Sofar"
DEVICE_IDENTIFIER = "sofar_123"
SENSOR_PREFIX_ID = "SF"

data_json = {
    MQTT_SENSOR_NAME: "SOC_Bat1",
    MQTT_SENSOR_ID: "2380228322_1544",
    MQTT_SENSOR_DEVICE_CLASS: "Battery",
    MQTT_SENSOR_PREFIX_ID: SENSOR_PREFIX_ID,
    MQTT_SENSOR_DEVICE_NAME: DEVICE_NAME,
    MQTT_SENSOR_DEVICE_IDENTIFIER: DEVICE_IDENTIFIER,
    MQTT_SENSOR_STATE: 52,
    MQTT_SENSOR_UNIT: "%",
}


ha_mqtt = HomeAssistantMQTT()
# ha_mqtt.discover_sensor(data_json)

pub = {
    REG_ADDR: "0x0608",
    REG_RATIO: 1.0,
    REG_TYPE: "U16",
    REG_UNIT: "%",
    REG_DEVICE_CLASS: "Battery",
    REG_TITLE: "Battery SOC",
    REG_VALUE: "68.0",
    REG_ID: "2380228322_1544",
    REG_FRIENDLY_NAME: "Battery voltage",
}

mapping = (
    (REG_FRIENDLY_NAME, MQTT_SENSOR_NAME),
    (REG_ID, MQTT_SENSOR_ID),
    (REG_DEVICE_CLASS, MQTT_SENSOR_DEVICE_CLASS),
    (REG_VALUE, MQTT_SENSOR_STATE),
    (REG_UNIT, MQTT_SENSOR_UNIT),
)

data_json = {
    MQTT_SENSOR_PREFIX_ID: SENSOR_PREFIX_ID,
    MQTT_SENSOR_DEVICE_NAME: DEVICE_NAME,
    MQTT_SENSOR_DEVICE_IDENTIFIER: DEVICE_IDENTIFIER,
}
for source, target in mapping:
    data_json[target] = pub.get(source, "")

print(data_json)
ha_mqtt.discover_sensor(data_json)
