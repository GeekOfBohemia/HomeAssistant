import os
import sys
import requests
import json
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from appframe.logger import app_log
from appframe.config_data import configData


class ApiComm:
    def __init__(self, url, endpoint):
        self._endpoint = endpoint
        self._headers = {"content-type": "application/json"}
        self._url = url
        self.system_ok: bool = True

    @property
    def url(self):
        return self._url + self._endpoint

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        pass

    def get(self, params):
        result = None
        self.system_ok = True
        try:
            result = requests.post(
                self.url, headers=self._headers, data=json.dumps(params), timeout=2
            )
        except:
            self.system_ok = False
        return result

    def post(self, payload: str, data: dict):
        url = f"{self.url}/{payload}"
        try:
            requests.post(url, headers=self._headers, data=json.dumps(data), timeout=2)
        except:
            current_datetime = datetime.datetime.now()

            # Format the date and time as a string
            cas = current_datetime.strftime("%d-%m-%Y %H:%M:%S")
            app_log.warning(cas + ": HA bez spojeni")
            app_log.warning(url)


class ApiHADirect(ApiComm):
    def __init__(self):
        super().__init__(configData.ha_url, "api")
        self._headers = {
            "Authorization": configData.ha_api_authorization,
            "Content-Type": "application/json",
        }

    def state(self, entity_id):
        url = f"{self.url}/states/{entity_id}"
        # Format the date and time as a string
        current_datetime = datetime.datetime.now()
        cas = current_datetime.strftime("%d-%m-%Y %H:%M:%S")
        try:
            result = requests.get(url, headers=self._headers, timeout=2)
            if result.status_code == 200:
                return json.loads(result.text)
        except:
            app_log.warning(cas + "HA bez spojeni")
            return None

    def services(self, payload: str, entity_id: str, data: dict = {}) -> bool:
        retval: bool = True
        url = f"{self.url}/services/{payload}"
        to_send: dict = {"entity_id": entity_id}
        if data:
            to_send.update(data)
        try:
            requests.post(
                url, headers=self._headers, data=json.dumps(to_send), timeout=2
            )
        except:
            retval = False
        return retval


if __name__ == "__main__":
    apiTest = ApiHADirect()
    l = apiTest.state("switch.garaz_topeni")
    print(l)
