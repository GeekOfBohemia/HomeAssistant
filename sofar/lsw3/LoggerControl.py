import binascii
import sys
import os
import socket
import libscrc

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lsw3.config_data import configData
from appframe.helpers import hex_zfill, padhex
from appframe.logger import app_log


class LoggerControl:
    def __init__(self):
        pass

    def read(self, pini, pfin):
        # Data logger frame begin
        retval = {}
        start = binascii.unhexlify("A5")  # Logger Start code
        length = binascii.unhexlify("1700")  # Logger frame DataLength
        controlcode = binascii.unhexlify("1045")  # Logger ControlCode
        serial = binascii.unhexlify("0000")  # Serial
        datafield = binascii.unhexlify(
            "020000000000000000000000000000"
        )  # com.igen.localmode.dy.instruction.send.SendDataField
        # Modbus request begin
        pos_ini = str(hex_zfill(pini)[2:])
        pos_fin = str(hex_zfill(pfin - pini + 1)[2:])
        businessfield = binascii.unhexlify(
            "0003" + pos_ini + pos_fin
        )  # Modbus data to count crc
        app_log.info(
            "Modbus request: 0103 "
            + pos_ini
            + " "
            + pos_fin
            + " "
            + str(padhex(hex(libscrc.modbus(businessfield)))[4:6])  # type: ignore
            + str(padhex(hex(libscrc.modbus(businessfield)))[2:4])  # type: ignore
        )

        crc = binascii.unhexlify(
            str(padhex(hex(libscrc.modbus(businessfield)))[4:6])  # type: ignore
            + str(padhex(hex(libscrc.modbus(businessfield)))[2:4])  # type: ignore
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
                return retval

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
                        return retval

                except socket.timeout as msg:
                    print("Connection timeout - inverter and/or gateway is off")
                    return retval

            # PARSE RESPONSE (start position 56, end position 60)
            assert data is not None
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
                retval[hexpos] = responsereg
                a += 1
        return retval
