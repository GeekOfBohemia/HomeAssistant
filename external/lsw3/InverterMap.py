# {
# 'Register address': {'0': '0x0484'}, 'Field': {'0': 'Frequency_Grid'},
# 'Type': {'0': 'U16'},
# 'Accuracy': {'0': 0.01},
# 'Unit': {'0': 'Hz'},
# 'Min': {'0': None},
# 'Max': {'0': None},
# 'Read/Write': {'0': 'R'},
# 'Remarks': {'0': 'Grid frequency'},
# 'User': {'0': 'End User'},
# 'title': {'0': 'Grid frequency'},
# 'metric_type': {'0': 'gauge'},
# 'metric_name': {'0': 'OutpuFreq'},
# 'label_name': {'0': 'Grid'},
# 'label_value': {'0': 'Frequency'}}


import os
import sys
import json
import pandas


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lsw3.globals import (
    REG_ADDR,
    REG_FRIENDLY_NAME,
    REG_ID,
    REG_DEVICE_CLASS,
    REG_RATIO,
    REG_STATE_CLASS,
    REG_TITLE,
    REG_TYPE,
    REG_UNIT,
    REG_VALUE,
)
from appframe.config_data import configData
from appframe.logger import app_log

MAP_REGISTER = "Register address"


from appframe.helpers import HelperOp

data_file_path = os.path.join(os.path.dirname(__file__), "registers.xlsx")

pd = pandas.read_excel(data_file_path, sheet_name="Source")
s: str = pd.to_json()
mapping: dict = json.loads(s)

for k, v in mapping[REG_ADDR].items():
    mapping[REG_ADDR][k] = HelperOp.h_fill(v)


def do_map(register, responsereg):
    retval = {}
    for k, v in mapping[REG_ADDR].items():
        if str(register) == v:
            for reg in (
                REG_ADDR,
                REG_TITLE,
                REG_RATIO,
                REG_TYPE,
                REG_UNIT,
                REG_DEVICE_CLASS,
                REG_FRIENDLY_NAME,
                REG_STATE_CLASS,
            ):
                retval[reg] = mapping[reg][k]

            value = 0
            if retval[REG_TYPE] == "U16":
                try:
                    value = int(str(responsereg), 16) * retval[REG_RATIO]
                except:
                    pass
            elif retval[REG_TYPE] == "I16":
                try:
                    value = HelperOp.twosComplement_hex(responsereg) * retval[REG_RATIO]
                except:
                    app_log.info(f"Chyba {responsereg}")
                    pass
            else:
                app_log.error("Neznámý typ")
            # print(f"Vysledek {value} z {responsereg}")
            retval[REG_VALUE] = str(round(value, 2))
            retval[REG_ID] = str(
                str(configData.inverter_sn) + "_" + str(int(retval[REG_ADDR], 16))
            )

            return retval


if __name__ == "__main__":
    print(mapping)
