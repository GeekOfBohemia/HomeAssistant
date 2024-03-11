# Revvised 02.10.2021 11:15
#
# WebSocket communication with HA
# https://developers.home-assistant.io/docs/api/websocket
#
# Dokumentace na
# https://websocket-client.readthedocs.io/en/latest/examples.html
#


from dataclasses import dataclass, field


import json
from multiprocessing import Queue
from typing import Union
import websocket  # type: ignore
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from appframe.ha_client import BasicClient


from appframe.type_def import CallableType, DictListDef, DictType, IntType, StrType
from appframe.helpers import HelperOp as h
from appframe.config_data import configData


MAX_BATCH = 10


class ws_error:
    NOT_OPEN = "error not open"
    RECEIVE_EMPTY_RAW = "error empty received"
    NOT_JSON = "Not json answer"
    AUTH_REQUIRED = "Authorization asked"
    OPEN = "open_error"
    NOT_PREPARED = "NOT_PREPARED"


# Sending data via ws_comm
@dataclass
class Cmd:
    unique_id: StrType = None
    cmd_data: dict = field(default_factory=dict)
    callback: CallableType = None
    comment: StrType = None
    id: int = 0
    sent: bool = False
    received: bool = False
    success: bool = False
    raw: DictType = None
    error_code: str = ""
    result: list = field(default_factory=list)
    repeat: bool = True
    finished: bool = False
    error_code: str = ""
    _cmd_json: StrType = None

    @property
    def cmd_json(self) -> str:
        if self._cmd_json is None:
            self._cmd_json = json.dumps(self.cmd_data)
        return self._cmd_json

    @cmd_json.setter
    def cmd_json(self, value):
        self._cmd_json = value

    @property
    def display_data(self) -> dict:
        return dict(
            unique_id=self.unique_id,
            cmd_data=self.cmd_data,
            error_code=self.error_code,
            raw=self.raw,
            sent=self.sent,
            finished=self.finished,
        )

    def update_id(self, new_id: int):
        self.id = new_id
        self.sent = False
        self.cmd_data.update({"id": new_id})
        self.cmd_json = None
        self.received = False
        self.repeat = False
        self.error_code = ""
        self.finished = False
        self.result.clear()


CmdType = Union[None, Cmd]


class WsHA(BasicClient):
    def __init__(self):
        self._cmd_register: dict = {}
        self._finished = False
        self._ws = None
        self._used_id: int = 0
        self.connection_error: bool = False
        self.fatal_error: bool = False
        self.at = configData.app_framework
        self._ws_url = os.path.join(
            f"ws://{configData.ha_ip}:{configData.ha_port}/", "api/websocket"
        )

    @property
    def _generator_type_id(self) -> IntType:
        self._used_id += 1
        if self._used_id > MAX_BATCH:
            return None
        else:
            return self._used_id

    def _done(self):
        self.ws_close()

    def _get_recv(self, cmd: Cmd) -> None:
        if self._ws is None:
            self.debug("None")
            cmd.error_code = ws_error.NOT_OPEN
            return None
        cmd.raw = self._ws.recv()  # type: ignore
        self.debug(f"Raw:{cmd.raw}")
        if cmd.raw is None:
            cmd.error_code = ws_error.RECEIVE_EMPTY_RAW
            return None
        cmd.received = True

        try:
            cmd.cmd_json = json.loads(cmd.raw)
        except:
            cmd.error_code = ws_error.NOT_JSON
            return

        auth = cmd.cmd_json.get("type", "")
        if auth == "auth_required":
            cmd.error_code = ws_error.AUTH_REQUIRED
            return

        id: StrType = cmd.cmd_json.get("id")
        if id is None:
            cmd.error_code = "return id None"
            return
        if int(id) != cmd.id:
            cmd.error_code = f"id returned {id}, should be: {cmd.id}"
            return
        cmd.result = cmd.cmd_json.get("result")
        if cmd.result is not None:
            cmd.success = cmd.cmd_json.get("success", False)

    def ws_close(self):
        if hasattr(self, "_ws"):
            if self._ws is not None:
                self._ws.close()
        self._ws = None
        self._used_id = 0

    def _check_connection(self) -> bool:
        self.debug("Checking connection inside")
        retval: bool = False
        if self.fatal_error:
            self.error("Fatal - token missing")
            return retval

        # if was connecion
        self.debug("Checking connection inside")
        if self._ws is not None:
            self.debug("Checking connection inside")
            if self._ws.connected:
                return True
            else:
                self.debug("Checking connection inside close")
                self.ws_close()
        self.debug("Checking connection inside continue")
        self.connection_error = False

        # part of opening connection
        self.debug(f"Checking connection inside here {self._ws_url}")
        try:
            self._ws = websocket.create_connection(self._ws_url)
        except TimeoutError:
            self._ws = None
            self.connection_error = True
            self.error("Timeout error connection")
            return False
        if self._ws is None:
            self.error("Nemam connection")
            return False
        self.debug(f"Asking for recv")
        recv = self._ws.recv()  # asking for authorization
        self.info(f"open received: {recv}")

        if recv is None:
            self.connection_error = True
            return False
        received: dict = json.loads(recv)
        auth = received.get("type", "")
        if auth != "auth_required":
            self.warning("Error in authentication")
            raise ValueError("Error in authentication")

        auth = {"type": "auth", "access_token": self.at}
        self.debug("Sending auth")
        self._ws.send(json.dumps(auth))
        recv = self._ws.recv()
        self.debug(f"Recieved{recv}")
        ret: dict = {}

        auth_result: str = ""
        if recv is not None:
            ret = json.loads(recv)
            auth_result = ret.get("type", "")
        if ret is None or auth_result != "auth_ok":
            self.warning("Error in authentication")
            raise ValueError("Error in authentication")
        else:
            retval = True
        return retval

    def prepare_for_send(self, cmd: Cmd) -> bool:
        # Checking - opening / close connection
        id: IntType = self._generator_type_id
        if id is None:
            self.ws_close()
        if self._ws is None:
            self.debug(f"Checking connection")
            retval = self._check_connection()
            if retval:
                id = self._generator_type_id
                if id is None:
                    self.error("Fatal in generator")
                    return False
        if id is not None:
            cmd.update_id(id)
            return True
        else:
            return False

    def _send_recieve_direct(self, cmd: Cmd) -> bool:
        """Called from MainLoop

        Args:
            cmd (Cmd): [description]

        Returns:
            Any: [description]
        """

        self.debug(f"Prepare {cmd.cmd_data}")

        # if return None - it means it is necessary close and re_open
        prepared: bool = self.prepare_for_send(cmd)
        if not prepared:
            return False
        if self._ws is None:
            return False
        # self.debug(f"done {cmd}")
        # self.debug(f"done {cmd.cmd_json}")
        self._ws.send(cmd.cmd_json)

        # Marking that it was sent
        cmd.sent = True
        self.debug(f"Was sent {cmd.cmd_json}")

        self._get_recv(cmd)
        if len(cmd.error_code) > 0:
            self.error(f"Mistake in communication {cmd.error_code}")
            return False
        return True

    def get_entities(self, domain: str) -> Cmd:
        """Return list of entities

        Args:
            domain (str): [description]

        Returns:
            dict: [description]
        """

        to_send = dict(type=domain + "/list")
        cmd: Cmd = Cmd(h.get_id(), cmd_data=to_send)
        self.debug(f"Asking: {to_send}")
        self._send_recieve_direct(cmd)
        return cmd


if __name__ == "__main__":
    wsHA = WsHA()
    wsHA._check_connection()
    cmd = wsHA.get_entities("input_boolean")
    print(cmd.finished)
