#!/usr/bin/python3
# Hlavni routina pro vyvoj
# Maximalni nabijeni baterie 2.1kW
import sys
import socket
import binascii
import libscrc
import os

import time


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from appframe.config_data import configData
from lsw3.InverterMap import do_map
from lsw3.globals import (
    REG_ADDR,
    REG_DEVICE_CLASS,
    REG_FRIENDLY_NAME,
    REG_ID,
    REG_UNIT,
    REG_VALUE,
)

from appframe.ha_client import HAClientApi

from appframe.helpers import HelperOp
from appframe.core_control import CoreControl
from appframe.logger import app_log
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

mapping = (
    (REG_FRIENDLY_NAME, MQTT_SENSOR_NAME),
    (REG_ID, MQTT_SENSOR_ID),
    (REG_DEVICE_CLASS, MQTT_SENSOR_DEVICE_CLASS),
    (REG_VALUE, MQTT_SENSOR_STATE),
    (REG_UNIT, MQTT_SENSOR_UNIT),
)

DEVICE_NAME = "Sofar"
DEVICE_IDENTIFIER = "sofar_123"
SENSOR_PREFIX_ID = "SF"


class DataReg(HAClientApi):
    def __init__(self):
        super().__init__()
        self.ha_mqtt = HomeAssistantMQTT()
        # Here is configuration what registers to read
        self.loop = [
            "0x0600",
            "0x0610",
            "0x03C0",
            "0x03CA",
            "0x0480",
            "0x04BC",
            "0x04BD",
            "0x04C0",
            "0x580",
            "0x05B4",
        ]

    def read(self):
        loop = self.loop.copy()
        while loop:

            pfin = int(loop.pop(-1), 0)
            pini = int(loop.pop(-1), 0)
            # Data logger frame begin
            start = binascii.unhexlify("A5")  # Logger Start code
            length = binascii.unhexlify("1700")  # Logger frame DataLength
            controlcode = binascii.unhexlify("1045")  # Logger ControlCode
            serial = binascii.unhexlify("0000")  # Serial
            datafield = binascii.unhexlify(
                "020000000000000000000000000000"
            )  # com.igen.localmode.dy.instruction.send.SendDataField
            # Modbus request begin
            pos_ini = str(HelperOp.hex_zfill(pini)[2:])
            pos_fin = str(HelperOp.hex_zfill(pfin - pini + 1)[2:])
            businessfield = binascii.unhexlify(
                "0003" + pos_ini + pos_fin
            )  # Modbus data to count crc
            app_log.info(
                "Modbus request: 0103 "
                + pos_ini
                + " "
                + pos_fin
                + " "
                + str(HelperOp.padhex(hex(libscrc.modbus(businessfield)))[4:6])  # type: ignore
                + str(HelperOp.padhex(hex(libscrc.modbus(businessfield)))[2:4])  # type: ignore
            )

            crc = binascii.unhexlify(
                str(HelperOp.padhex(hex(libscrc.modbus(businessfield)))[4:6])  # type: ignore
                + str(HelperOp.padhex(hex(libscrc.modbus(businessfield)))[2:4])  # type: ignore
            )  # CRC16modbus
            # Modbus request end
            checksum = binascii.unhexlify("00")  # checksum F2
            endCode = binascii.unhexlify("15")  # Logger End code
            inverter_sn2 = bytearray.fromhex(
                hex(configData.inverter_sn)[8:10]
                + hex(configData.inverter_sn)[6:8]
                + hex(configData.inverter_sn)[4:6]
                + hex(configData.inverter_sn)[2:4]
            )
            frame = bytearray(
                start
                + length
                + controlcode
                + serial
                + inverter_sn2
                + datafield
                + businessfield
                + crc
                + checksum
                + endCode
            )

            app_log.info(
                "Hex string to send: A5 1700 1045 0000 "
                + hex(configData.inverter_sn)[8:10]
                + hex(configData.inverter_sn)[6:8]
                + hex(configData.inverter_sn)[4:6]
                + hex(configData.inverter_sn)[2:4]
                + " 020000000000000000000000000000 "
                + "0104"
                + pos_ini
                + pos_fin
                + str(hex(libscrc.modbus(businessfield))[3:5])  # type: ignore
                + str(hex(libscrc.modbus(businessfield))[2:3].zfill(2))  # type: ignore
                + " 00 15"
            )

            app_log.info(f"Data sent: {frame}")
            # Data logger frame end

            checksum = 0
            frame_bytes = bytearray(frame)
            for i in range(1, len(frame_bytes) - 2, 1):
                checksum += frame_bytes[i] & 255
            frame_bytes[len(frame_bytes) - 2] = int((checksum & 255))

            # OPEN SOCKET
            for res in socket.getaddrinfo(
                configData.inverter_ip,
                configData.inverter_port,
                socket.AF_INET,
                socket.SOCK_STREAM,
            ):
                family, socktype, proto, canonname, sockadress = res
                try:
                    clientSocket = socket.socket(family, socktype, proto)
                    clientSocket.settimeout(15)
                    clientSocket.connect(sockadress)
                except socket.error as msg:
                    app_log.info("Could not open socket - inverter/logger turned off")
                    return

                # SEND DATA
                clientSocket.sendall(frame_bytes)

                ok: bool = False
                data = None
                while not ok:
                    try:
                        data = clientSocket.recv(1024)
                        ok = True
                        if data is None:
                            ok = False
                            return

                    except:
                        self.warning(
                            "Connection timeout - inverter and/or gateway is off"
                        )
                        return

                # PARSE RESPONSE (start position 56, end position 60)
                if data is None:
                    return
                app_log.info(f"Data received: {data}")
                i = pfin - pini  # Number of registers
                a = 0  # Loop counter
                response = str(
                    "".join(hex(ord(chr(x)))[2:].zfill(2) for x in bytearray(data))
                )  # +'  '+re.sub('[^\x20-\x7f]', '', '')));

                hexstr = str(
                    " ".join(hex(ord(chr(x)))[2:].zfill(2) for x in bytearray(data))
                )
                app_log.info(f"Hex string received: {hexstr.upper()}")

                while a <= i:
                    p1 = 56 + (a * 4)
                    p2 = 60 + (a * 4)
                    responsereg = response[p1:p2]
                    # print(p1, p2, responsereg)
                    hexpos = str("0x") + str(hex(a + pini)[2:].zfill(4)).upper()
                    try:
                        v = int(str(responsereg), 16) * 0.01
                    except:
                        v = 0
                    app_log.info(
                        f"Register: {hexpos} value: hex: {responsereg} value: {v}"
                    )
                    reg = do_map(hexpos, responsereg)
                    if reg is not None:
                        # print(reg)
                        data_json = {
                            MQTT_SENSOR_PREFIX_ID: SENSOR_PREFIX_ID,
                            MQTT_SENSOR_DEVICE_NAME: DEVICE_NAME,
                            MQTT_SENSOR_DEVICE_IDENTIFIER: DEVICE_IDENTIFIER,
                        }
                        for source, target in mapping:
                            data_json[target] = reg.get(source, "")

                        self.ha_mqtt.discover_sensor(data_json)
                    a += 1


if __name__ == "__main__":
    ls = DataReg()
    ls.start()
    while not CoreControl.stop_flag:
        time.sleep(1)
    ls.stop()
