"""StarLine device."""
from typing import Optional, Dict, Any, List
from .const import (
    BATTERY_LEVEL_MIN,
    BATTERY_LEVEL_MAX,
    GSM_LEVEL_MIN,
    GSM_LEVEL_MAX,
    DEVICE_FUNCTION_POSITION,
    DEVICE_FUNCTION_STATE,
)
from datetime import datetime

class StarlineDevice:
    """StarLine device class."""

    def __init__(self):
        """Constructor."""
        self._device_id: Optional[str] = None
        self._imei: Optional[str] = None
        self._alias: Optional[str] = None
        self._battery: Optional[int] = None
        self._ctemp: Optional[int] = None
        self._etemp: Optional[int] = None
        self._fw_version: Optional[str] = None
        self._gsm_lvl: Optional[int] = None
        self._phone: Optional[str] = None
        self._status: Optional[int] = None
        self._ts_activity: Optional[float] = None
        self._typename: Optional[str] = None
        self._balance: Dict[str, Dict[str, Any]] = {}
        self._car_state: Dict[str, bool] = {}
        self._car_alr_state: Dict[str, bool] = {}
        self._functions: List[str] = []
        self._position: Dict[str, float] = {}
        self._fuel: Dict[str, Any] = {}
        self._errors: Dict[str, Any] = {}
        self._mileage: Dict[str, Any] = {}
        self._motohrs: Dict[str, Any] = {}
    def update(self, device_data):
        """Обновление данных устройства из нового JSON."""
        # Генерируем временную метку для логов
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        _LOGGER.debug(f"[{current_time}] [StarlineDevice] Начало разбора JSON для устройства {self.name}")

        try:
            # Парсим новую структуру (данные лежат внутри ключа "data", если он есть, 
            # либо device_data уже является словарем "data")
            data = device_data.get("data", device_data)
            
            self._imei = data.get("imei")
            self._alias = data.get("alias")
            
            # Маппинг телематики из блока common и obd
            common_data = data.get("common", {})
            obd_data = data.get("obd", {})
            
            self._battery = common_data.get("battery")
            self._ctemp = common_data.get("ctemp")
            self._etemp = common_data.get("etemp")
            self._fuel_percent = obd_data.get("fuel_percent")

            # Маппинг статусов. Сохраняем в _car_state, чтобы не ломать старый код HA!
            self._car_state = data.get("state", {})
            self._car_alrm_state = data.get("alarm_state", {})
            
            # Вытягиваем моточасы напрямую
            self._motohrs = self._car_state.get("motohrs")
            
            self._fw_version = data.get("firmware_version")
            self._gsm_lvl = common_data.get("gsm_lvl")
            self._phone = data.get("telephone")
            self._status =  data.get("status")
            self._ts_activity = data.get("activity_ts")
            self._typename = data.get("typename")
            self._balance = data.get("balance", {})
            self._functions = data.get("functions", [])
            self._position = data.get("position")
            self._mileage = obd_data.get("mileage")
            _LOGGER.debug(f"[{current_time}] [StarlineDevice] Успешно распарсено: Батарея={self._battery}, Моточасы={self._motohrs}")

        except Exception as e:
            _LOGGER.error(f"[{current_time}] [StarlineDevice] Ошибка разбора JSON: {e}", exc_info=True)

    def update_obd(self, obd_info):
        """Update OBD data from server."""
        self._fuel = obd_info.get("fuel")
        self._errors = obd_info.get("errors")
        self._mileage = obd_info.get("mileage")

    def update_car_state(self, car_state):
        """Update car state from server."""
        for key in car_state:
            if key in self._car_state:
                self._car_state[key] = car_state[key] in ["1", "true", True]

    @property
    def support_position(self):
        """Is position supported by this device."""
        return DEVICE_FUNCTION_POSITION in self._functions and self._position

    @property
    def support_state(self):
        """Is state supported by this device."""
        return DEVICE_FUNCTION_STATE in self._functions and self._car_state

    @property
    def device_id(self):
        """Device ID."""
        return self._device_id

    @property
    def fw_version(self):
        """Firmware version."""
        return self._fw_version

    @property
    def name(self):
        """Device name."""
        return self._alias

    @property
    def typename(self):
        """Device type name."""
        return self._typename

    @property
    def position(self):
        """Car position."""
        return self._position

    @property
    def online(self):
        """Is device online."""
        return int(self._status) == 1

    @property
    def battery_level(self):
        """Car battery level."""
        return self._battery

    @property
    def battery_level_percent(self):
        """Car battery level percent."""
        if self._battery is None:
            return 0
        if self._battery > BATTERY_LEVEL_MAX:
            return 100
        if self._battery < BATTERY_LEVEL_MIN:
            return 0
        return round(
            (self._battery - BATTERY_LEVEL_MIN)
            / (BATTERY_LEVEL_MAX - BATTERY_LEVEL_MIN)
            * 100
        )

    @property
    def balance(self):
        """Device balance."""
        return self._balance.get("active", {})

    @property
    def car_state(self):
        """Car state."""
        return self._car_state

    @property
    def alarm_state(self):
        """Car alarm level."""
        return self._car_alr_state

    @property
    def temp_inner(self):
        """Car inner temperature."""
        return self._ctemp

    @property
    def temp_engine(self):
        """Engine temperarure."""
        return self._etemp

    @property
    def gsm_level(self):
        """GSM signal level."""
        if self._gsm_lvl is None:
            return None
        if not self.online:
            return 0
        return self._gsm_lvl

    @property
    def gsm_level_percent(self):
        """GSM signal level percent."""
        if self.gsm_level is None:
            return None
        if self.gsm_level > GSM_LEVEL_MAX:
            return 100
        if self.gsm_level < GSM_LEVEL_MIN:
            return 0
        return round(
            (self.gsm_level - GSM_LEVEL_MIN) / (GSM_LEVEL_MAX - GSM_LEVEL_MIN) * 100
        )

    @property
    def imei(self):
        """Device IMEI."""
        return self._imei

    @property
    def phone(self):
        """Device phone number."""
        return self._phone

    @property
    def fuel(self):
        """Device fuel count."""
        return self._fuel

    @property
    def errors(self):
        """Device errors info."""
        return self._errors

    @property
    def mileage(self):
        """Device mileage count."""
        return self._mileage
        
    @property
    def motohrs(self):
        """Device motohrs count."""
        return self._motohrs
