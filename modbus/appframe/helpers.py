from enum import Enum
import datetime
import os
from typing import Any, List, Union
import uuid
from pathlib import Path

from appframe.type_def import DictKeys

OFF = "off"
ON = "on"

DictType = Union[None, dict]


class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):  # type:ignore
        return name


HA_HELPERS: tuple = ("input_boolean", "input_number", "input_text", "input_button")


class HelperOp:
    @staticmethod
    def entity_id(domain: str, name: str) -> str:
        return f"{domain}.{name}"

    @staticmethod
    def is_array(myvar: Any) -> bool:
        if myvar is None:
            return False
        return isinstance(myvar, list) or isinstance(myvar, tuple)

    @staticmethod
    def split_entity(entity_id: str):
        return entity_id.split(".")

    @staticmethod
    def get_id() -> str:
        return uuid.uuid4().hex

    @staticmethod
    def get_project_root() -> Path:
        return Path(__file__).parent.parent

    @staticmethod
    def filename(name: str) -> str:
        return os.path.join(HelperOp.get_project_root(), name)

    @staticmethod
    def h_fill(hexvalue) -> str:
        return "0x" + str(hexvalue).zfill(4)

    @staticmethod
    def padhex(s):
        return "0x" + s[2:].zfill(4)

    @staticmethod
    def hex_zfill(intval):
        hexvalue = hex(intval)
        return "0x" + str(hexvalue)[2:].zfill(4)

    @staticmethod
    def get_iso_timestamp() -> str:
        return f"{datetime.datetime.utcnow().isoformat()}+00:00"

    @staticmethod
    def twosComplement_hex(hexval) -> int:
        bits = 16
        val = int(hexval, bits)
        if val & (1 << (bits - 1)):
            val -= 1 << bits
        return val

    @staticmethod
    def in_array(to_search: str, arr: Union[list, DictKeys]) -> bool:
        if isinstance(arr, list):
            try:
                a = arr.index(to_search)
                return True
            except:
                return False
        elif isinstance(arr, dict):
            try:
                return HelperOp.in_array(to_search, list(arr.keys()))
            except:
                raise ValueError("Wrong argument in_array")

    @staticmethod
    def remove_key(
        param: Union[list, dict], key: Union[str, List[str]], default: Any = None
    ) -> Any:
        """Delete from dictionary or list with key

        Args:
            param (list|dict): source
            key (type): to be pop
        Returns:
            type: without key
        """
        retval_list: list = []
        retval = default
        if isinstance(key, list):
            for k in key:
                retval_list.append(HelperOp.remove_key(param, k))
            return retval_list
        if isinstance(param, list) and isinstance(key, str):
            if HelperOp.in_array(key, param):
                retval = key
                param.remove(key)
        elif isinstance(param, dict) and isinstance(key, str):
            if key in param.keys():
                retval = param.get(key, default)
                del param[key]
        return retval


if __name__ == "__main__":
    print(HelperOp.filename("Config"))
