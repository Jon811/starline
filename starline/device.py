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
import logging
_LOGGER = logging.getLogger(__name__)

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
        """Update device data from API response."""
        import logging
        from datetime import datetime
        _LOGGER = logging.getLogger(__name__)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Распаковываем ответ
        data = device_data.get("data", device_data)
        
        try:
            # 1. БАЗОВЫЕ ИДЕНТИФИКАТОРЫ
            if "device_id" in data:
                self._device_id = str(data["device_id"])
            if "imei" in data:
                self._imei = data["imei"]
            if "alias" in data:
                self._alias = data["alias"]
            if "typename" in data:
                self._typename = data["typename"]
            if "status" in data:
                self._status = int(data["status"])
            if "firmware_version" in data:
                self._fw_version = data["firmware_version"]
            if "telephone" in data:
                self._phone = data["telephone"]
                
            # 2. ФУНКЦИИ (Критично важно для появления switch и button в HA!)
            if "functions" in data:
                self._functions = data["functions"]

            # 3. ПОЗИЦИЯ НА КАРТЕ
            if "position" in data:
                self._position = data["position"]

            # 4. БАЛАНС (Адаптация списка v3 под структуру v2 и фикс времени)
            if "balance" in data:
                balance_data = data["balance"]
                if isinstance(balance_data, list):
                    parsed_balance = {}
                    for item in balance_data:
                        key = item.get("key", "active")
                        
                        # Превращаем Unix Timestamp (число) в строку ISO8601
                        ts = item.get("ts")
                        if isinstance(ts, (int, float)):
                            from datetime import datetime, timezone
                            # Конвертируем 1779009708 -> "2026-05-02T12:01:48+00:00"
                            item["ts"] = datetime.fromtimestamp(ts, timezone.utc).isoformat()
                            
                        parsed_balance[key] = item
                    self._balance = parsed_balance
                elif isinstance(balance_data, dict):
                    self._balance = balance_data
                else:
                    self._balance = {}

            # 5. ТЕЛЕМАТИКА (Температура, батарея, связь)
            common = data.get("common", {})
            if "battery" in common:
                self._battery = common["battery"]
            if "ctemp" in common:
                self._ctemp = common["ctemp"]
            if "etemp" in common:
                self._etemp = common["etemp"]
            if "gsm_lvl" in common:
                self._gsm_lvl = common["gsm_lvl"] 
            if "gps_lvl" in common:
                self._gps_level = common["gps_lvl"] 

            # 6. OBD (Топливо, пробег)
            obd = data.get("obd", {})
            if "fuel_percent" in obd:
                # В старом API топливо тоже было словарем с ключом val
                self._fuel_percent = {"val": obd["fuel_percent"]} 
            if "mileage" in obd:
                # Оборачиваем число в словарь, чтобы работал метод get("val")
                self._mileage = {"val": obd["mileage"]}

            # 7. СОСТОЯНИЯ И МОТОЧАСЫ
            if "state" in data:
                self._car_state = data["state"]
                self._motohrs = self._car_state.get("motohrs")/60
                # Агрегация всех дверей в один общий статус
                any_door_open = (
                    self._car_state.get("door", False) or 
                    self._car_state.get("front_pass_door", False) or 
                    self._car_state.get("rear_left_door", False) or 
                    self._car_state.get("rear_right_door", False)
                )
                # Принудительно перезаписываем главный ключ "door", 
                # который читает Home Assistant
                self._car_state["door"] = any_door_open
            if "alarm_state" in data:
                self._car_alrm_state = data["alarm_state"]
                
            _LOGGER.debug(f"[{current_time}] [StarlineDevice] Успешно распарсены все расширенные данные для {self._device_id}")

        except Exception as e:
            _LOGGER.error(f"[{current_time}] [StarlineDevice] Ошибка разбора данных v3: {e}", exc_info=True)

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
