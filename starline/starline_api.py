"""Data StarLine API."""
import logging
from typing import Dict, List, Callable, Optional, Any
from .base_api import BaseApi
from .device import StarlineDevice

_LOGGER = logging.getLogger(__name__)


class StarlineApi(BaseApi):
    """Data StarLine API class."""

    def __init__(self, user_id: str, slnet_token: str):
        """Constructor."""
        super().__init__()
        self._user_id: str = user_id
        self._slnet_token: str = slnet_token
        self._devices: Dict[str, StarlineDevice] = {}
        self._available: bool = False
        self._update_listeners: List[Callable] = []

    def _call_listeners(self) -> None:
        """Call listeners for update notifications."""
        for listener in self._update_listeners:
            listener()

    def add_update_listener(self, listener: Callable) -> Callable:
        """Add a listener for update notifications."""
        def dispose_():
            self._update_listeners.remove(listener)

        self._update_listeners.append(listener)
        return dispose_

    def update(self) -> None:
        """Update StarLine data."""
        devices = self.get_user_info()
        if not devices:
            self._available = False
        else:
            self._available = True
            for device_data in devices:
                device_id = str(device_data["device_id"])
                if device_id not in self._devices:
                    self._devices[device_id] = StarlineDevice()
                self._devices[device_id].update(device_data)

        self._call_listeners()

    def update_obd(self) -> None:
        """Update OBD data."""
        if not self._available:
            return None

        url = "https://developer.starline.ru/json/v1/device/{}/obd_params"
        headers = {"Cookie": "slnet=" + self._slnet_token}
        for device_id in self._devices:
            response = self._get(url.format(device_id), headers=headers)
            if response is None:
                continue

            code = int(response["code"])
            if code != 200:
                continue

            data = response["obd_params"]
            if "errors" in data and data["errors"] and data["errors"]["val"] > 0:
                data["errors"]["errors"] = self.get_obd_errors(device_id)

            self._devices[device_id].update_obd(data)

    @property
    def devices(self) -> Dict[str, StarlineDevice]:
        """Devices list."""
        return self._devices

    @property
    def available(self) -> bool:
        """Is data available"""
        return self._available

    def get_user_info(self) -> Optional[List[Dict[str, Any]]]:
"""Get user information (Modified for v1 API with extended parameters)."""
        from datetime import datetime
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        url = "https://developer.starline.ru/json/v1/user/{}/deviceList?imei=true&alias=true&pos=true&status=true".format(self._user_id)
        headers = {"Cookie": "slnet=" + self._slnet_token}
        
        _LOGGER.debug(f"[{current_time}] [StarlineApi] [v1_DEVICE_LIST] Отправка запроса. URL: {url}")
        
        response = self._get(url, headers=headers)
        
        current_time_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        if response is None:
            _LOGGER.error(f"[{current_time_end}] [StarlineApi] [v1_DEVICE_LIST] Ошибка: Получен пустой ответ от сервера.")
            return None

        try:
            code = int(response.get("code", 0))
        except ValueError:
            code = 0

        if code == 200:
            data = response.get("data", {})
            devices = data.get("devices", [])
            _LOGGER.debug(f"[{current_time_end}] [StarlineApi] [v1_DEVICE_LIST] Успех. Найдено устройств: {len(devices)}. Данные: {devices}")
            return devices
            
        _LOGGER.warning(f"[{current_time_end}] [StarlineApi] [v1_DEVICE_LIST] Неожиданный код {code}. Ответ: {response}")
        return None

    def get_device_data_v3(self, device_id: str) -> Optional[dict]:
        """Get extended device data via v3 API (Custom implementation)."""
        from datetime import datetime
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        url = "https://developer.starline.ru/json/v3/device/{}/data".format(device_id)
        headers = {"Cookie": "slnet=" + self._slnet_token}
        _LOGGER.debug(f"[{current_time}] [StarlineApi] [v3_DATA] Запрос полной телематики для устройства {device_id}. URL: {url}")
        response = self._get(url, headers=headers)
        current_time_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        if response is None:
            _LOGGER.error(f"[{current_time_end}] [StarlineApi] [v3_DATA] Ошибка: Пустой ответ для {device_id}")
            return None
        try:
            code = int(response.get("code", 0))
        except ValueError:
            code = 0
        if code == 200:
            _LOGGER.debug(f"[{current_time_end}] [StarlineApi] [v3_DATA] Успех. Код 200 получен.")
            return response
        _LOGGER.warning(f"[{current_time_end}] [StarlineApi] [v3_DATA] Неожиданный код ответа {code}. Ответ: {response}")
        return None

    def get_obd_errors(self, device_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get obd device errors."""
        url = "https://developer.starline.ru/json/v1/device/{}/obd_errors".format(device_id)
        headers = {"Cookie": "slnet=" + self._slnet_token}
        response = self._get(url, headers=headers)
        if response is None:
            return None

        code = int(response["code"])
        if code == 200:
            return response["obd_errors"]
        return None

    def set_car_state(self, device_id: str, name: str, state: bool):
        """Set car state information."""
        _LOGGER.debug("Setting car %s state: %s=%d", device_id, name, state)
        url = "https://developer.starline.ru/json/v1/device/{}/set_param".format(device_id)
        data = {"type": name, name: 1 if state else 0}
        headers = {"Cookie": "slnet=" + self._slnet_token}
        response = self._post(url, json=data, headers=headers)
        if response is None:
            return None

        code = int(response["code"])
        if code == 200:
            self._devices[device_id].update_car_state(response)
            self._call_listeners()
            return response
        return None

    def set_user_id(self, user_id: str) -> None:
        """Update user ID."""
        self._user_id = user_id

    def set_slnet_token(self, slnet_token: str) -> None:
        """Update SLNet token."""
        self._slnet_token = slnet_token
