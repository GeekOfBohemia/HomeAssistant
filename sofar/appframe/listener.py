from abc import abstractmethod
from dataclasses import dataclass, field
from enum import auto
import sys
import os
import uuid
from typing import Any

from overrides import override


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from appframe.ha_client import HAClientApi
from appframe.helpers import AutoName

OFF = "off"
ON = "on"


class CB_LISTENER_STATE(AutoName):
    ON = auto()
    OFF = auto()
    ON_OFF = auto()


@dataclass
class ListenElement:
    handler: Any = None
    old_state: Any = None
    state: Any = None
    callback: Any = None
    entity_id: str = field(default="")

    def __post_init__(self):
        self.handler = uuid.uuid4().hex

    @abstractmethod
    def state_changed(self, old_state, new_state) -> None:
        ...


class ListenOn(ListenElement):
    @override
    def state_changed(self, old_state, new_state) -> None:
        if old_state == OFF and new_state == ON:
            self.callback()


class ListenOff(ListenElement):
    @override
    def state_changed(self, old_state, new_state) -> None:
        if old_state == ON and new_state == OFF:
            self.callback()


class ListenButton(ListenElement):
    def state_changed(self, old_state, new_state) -> None:
        self.callback()


class ListenState(ListenElement):
    def state_changed(self, old_state, new_state) -> None:
        self.callback()


class Listener(HAClientApi):
    def __init__(self):
        super().__init__()
        self._elements: dict = {}

    def remove_handler(self, handler) -> None:
        if isinstance(handler, list):
            for h in handler:
                del self._elements[h]
        else:
            del self._elements[handler]

    def add_element(self, le: ListenElement):
        le.state = self.get_state(le.entity_id)
        le.old_state = le.state
        self._elements[le.handler] = le
        return le.handler

    @override
    def read(self):
        le: ListenElement
        try:
            for _, le in self._elements.items():
                new_state = self.get_state(le.entity_id)
                # print(f"old_state: {le.old_state} {new_state}")

                if new_state != le.old_state:
                    le.state_changed(le.old_state, new_state)
                    le.old_state = new_state
        except:
            pass

    def set_on(self, entity_id, callback):
        el_on: ListenOn = ListenOn(
            entity_id=entity_id,
            callback=callback,
        )
        return self.add_element(el_on)

    def set_off(self, entity_id, callback):
        el_off: ListenOff = ListenOff(
            entity_id=entity_id,
            callback=callback,
        )
        return self.add_element(el_off)

    def button_on(self, entity_id, callback):
        el_button: ListenButton = ListenButton(
            entity_id=entity_id,
            callback=callback,
        )
        return self.add_element(el_button)

    def set_state_changed(self, entity_id, callback):
        el_button: ListenState = ListenState(
            entity_id=entity_id,
            callback=callback,
        )
        return self.add_element(el_button)

    @override
    def get_interval_loop(self) -> int:
        return 1


class EntityController(Listener):
    def __init__(self):
        super().__init__()


lsn: Listener = Listener()
lsn.start()
