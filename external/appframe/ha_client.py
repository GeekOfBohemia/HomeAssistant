from abc import abstractmethod
import threading
import time
import sys
import os
from typing import Any, Union
import datetime

from overrides import override


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from appframe.core_control import CoreControl
from appframe.api_comm import ApiHADirect
from appframe.logger import app_log
from appframe.helpers import ON, OFF, HelperOp
from appframe.type_def import BasicEntity


def format_timedelta(delta):
    days, seconds = delta.days, delta.seconds
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Customize the format as needed
    formatted_time = "{:02}:{:02}:{:02}".format(hours, minutes, seconds)

    if days > 0:
        formatted_time = "{} days, {}".format(days, formatted_time)

    return formatted_time


def timedelta_sec(delta) -> float:
    days, seconds = delta.days, delta.seconds
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    retval: float = days * 24 * 60 * 60
    retval += hours * 60 * 60
    retval += minutes * 60
    retval += seconds

    return retval


class BasicClient:
    def get_timestamp(self) -> str:
        # Get the current date and time
        current_datetime = datetime.datetime.now()

        # Format the date and time as a string
        return current_datetime.strftime("%d-%m-%Y %H:%M:%S")

    def debug(self, msg: Any) -> None:
        app_log.debug(msg)

    def error(self, msg: str) -> None:
        app_log.error(self.get_timestamp() + " " + msg)

    def info(self, msg: str) -> None:
        app_log.info(self.get_timestamp() + " " + msg)

    def warning(self, msg: str) -> None:
        app_log.warning(self.get_timestamp() + " " + msg)


class HaClient(BasicClient):
    def start(self):
        self._thread = threading.Thread(target=self.run)
        self._thread.start()

    def stop(self):
        self._thread.join()

    def get_interval_loop(self) -> int:
        return 30

    @abstractmethod
    def read(self): ...

    def run(self, *args):
        while not CoreControl.stop_flag:
            self.read()
            i = 0
            while i < self.get_interval_loop():
                i += 1
                if CoreControl.stop_flag:
                    return
                time.sleep(0.1)


class HAClientApi(HaClient):
    def __init__(self):
        self._api = ApiHADirect()
        self.init()

    def init(self):
        pass

    def set_sensor_binary(self, entity_id, value: bool, attributes=None):
        to_set = OFF
        if value:
            to_set = ON
        self.set_sensor(entity_id, to_set, attributes)

    def set_state(self, entity_id, state):
        attr: dict = {}
        response = self.state(entity_id)
        if response is not None:
            attr = response.get("attributes", {})
        self._api.post(
            f"states/{entity_id}",
            {
                "state": state,
                "attributes": attr,
            },
        )

    def set_mqtt_sensor(self, entity_id, state, attributes=None):
        response = self.state(entity_id)

    def set_sensor(self, entity_id, state, attributes=None):
        response = self.state(entity_id)

        if response is None:
            if attributes is None:
                self.set_state(entity_id, state)
            else:
                self._api.post(
                    f"states/{entity_id}",
                    {
                        "state": state,
                        "attributes": attributes,
                    },
                )
        else:
            attr: dict = response.get("attributes", {})
            if attributes is not None:
                attr.update(attributes)

            self._api.post(
                f"states/{entity_id}",
                {
                    "state": state,
                    "attributes": attr,
                },
            )

    def set_sensor_attr(self, entity_id, attr):
        s = self.state(entity_id)
        if isinstance(s, dict):
            state = s.get("state")
        else:
            state = ""
        if isinstance(s, dict):
            attributes: dict = s.get("attributes", {})
            attributes.update(attr)
            s["attributes"] = attributes
        else:
            attributes = {}
        self.set_sensor(entity_id, state, attributes)

    def state_extract_attr(self, entity_id, attr_name) -> str:
        s = self.state(entity_id)
        if isinstance(s, dict):
            return s.get(attr_name, "")
        else:
            return ""

    def get_last_update(self, entity_id) -> Union[datetime.datetime, None]:
        all_state = self.state(entity_id)
        if all_state is not None:
            s_last_updated = all_state["last_updated"][
                :19
            ]  # 2019-08-05T19:22:40.626824+00:00
            lu = datetime.datetime.strptime(s_last_updated, "%Y-%m-%dT%H:%M:%S")
            # zde je potreba upravit letni a zimni cas
            return lu + datetime.timedelta(hours=1)
        else:
            return None

    def s_get_last_update(self, entity_id: str) -> str:
        """Returning in string last update

        Args:
            entity_id (str): _description_

        Returns:
            str: _description_
        """
        retval = self.get_last_update(entity_id)
        if retval is None:
            return ""
        else:
            return retval.strftime("%Y-%m-%dT%H:%M:%S")

    def get_last_update_sec(self, entity_id: str) -> str:
        last_updated = self.get_last_update(entity_id)
        if last_updated is None:
            return "0"
        else:
            change = datetime.datetime.now() - last_updated

            return format_timedelta(change)

    def get_last_update_sec_float(self, entity_id: str) -> float:
        last_updated = self.get_last_update(entity_id)
        if last_updated is None:
            return 0
        else:
            change = datetime.datetime.now() - last_updated
            return timedelta_sec(change)

    def state_extract(self, entity_id) -> str:
        return self.state_extract_attr(entity_id, "state")

    def state(self, entity_id):
        return self._api.state(entity_id)

    def last_updated(self, entity_id):
        return self.state_extract_attr(entity_id, "last_updated")

    def get_state(self, entity_id):
        return self.state_extract(entity_id)

    def get_state_int(self, entity_id) -> int:
        s = self.state_extract(entity_id)
        # print(f"entity_id: {entity_id} {s}")

        if s:
            retval = 0
            try:
                retval = int(float(s))
            except:
                retval = 0
            return retval
        else:
            return 0

    def is_entity_on(self, entity_id) -> bool:
        return self.state_extract(entity_id) == ON

    def is_entity_off(self, entity_id) -> bool:
        return self.state_extract(entity_id) == OFF

    def get_state_float(self, entity_id) -> float:
        s = self.state_extract(entity_id)
        if s:
            retval = 0
            try:
                retval = float(s)
            except:
                retval = 0
            return retval
        else:
            return 0

    def get_state_str(self, entity_id) -> str:
        s = self.state_extract(entity_id)
        if s:
            retval = ""
            try:
                retval = s
            except:
                retval = ""
            return retval
        else:
            return ""

    def turn_on(self, entity_id):
        domain, _ = entity_id.split(".")
        self._api.services(f"{domain}/turn_on", entity_id)

    def turn_off(self, entity_id: Union[str, list, BasicEntity, None]):
        if entity_id is None:
            return
        if isinstance(entity_id, BasicEntity):
            self.turn_off(entity_id.entity_id)
        else:
            if HelperOp.is_array(entity_id):
                for e in entity_id:
                    self.turn_off(e)
            elif isinstance(entity_id, str):
                domain, _ = entity_id.split(".")
                self._api.services(f"{domain}/turn_off", entity_id)

    def set_number(self, entity_id, value):
        self._api.services("number/set_value", entity_id, {"value": value})


if __name__ == "__main__":
    haClient = HAClientApi()
