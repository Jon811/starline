"""StarLine device."""
from typing import Optional, Dict, Any, List
from .const import (
    BATTERY_LEVEL_MIN,
    BATTERY_LEVEL_MAX,
    GSM_LEVEL_MIN,
    GSM_LEVEL_MAX,
)


class StarlineDevice:
    """StarLine device class."""

    def __init__(self):
        """Constructor."""
        self._device_id: Optional[str] = None
        self._alias: Optional[str] = None
        self._battery: Optional[int] = None
        self._ctemp: Optional[int] = None
        self._etemp: Optional[int] = None
        self._fw_version: Optional[str] = None
        self._gsm_lvl: Optional[int] = None
        self._gps_count: Optional[int] = None
        self._phone: Optional[str] = None
        self._status: Optional[int] = None
        self._ts_activity: Optional[float] = None
        self._typename: Optional[str] = None
        self._balance: List[Dict[str, Any]] = []
        self._car_state: Dict[str, bool] = {}
        self._car_alr_state: Dict[str, bool] = {}
        self._position: Dict[str, float] = {}
        self._fuel_litres: Optional[int] = None
        self._fuel_percent: Optional[int] = None
        self._mileage: Optional[int] = None

    def update(self, device_data):
        """Update data from server."""
        common = device_data.get("common", {})
        obd = device_data.get("obd", {})

        self._device_id = str(device_data.get("device_id"))
        self._alias = device_data.get("alias")
        self._battery = common.get("battery")
        self._ctemp = common.get("ctemp", common.get("mayak_temp"))
        self._etemp = common.get("etemp")
        self._fw_version = device_data.get("firmware_version")
        self._gsm_lvl = common.get("gsm_lvl")
        self._gps_count = common.get("gps_lvl")
        self._phone = device_data.get("telephone")
        self._status = device_data.get("status")
        self._ts_activity = device_data.get("activity_ts")
        self._typename = device_data.get("typename")
        self._balance = device_data.get("balance", [])
        self._car_state = device_data.get("state", {})
        self._car_alr_state = device_data.get("alarm_state", {})
        self._position = device_data.get("position")

        self._fuel_litres = obd.get("fuel_litres")
        self._fuel_percent = obd.get("fuel_percent")
        self._mileage = obd.get("mileage")

    def update_car_state(self, car_state):
        """Update car state from server."""
        for key in car_state:
            if key in self._car_state:
                self._car_state[key] = car_state[key] in ["1", "true", True]

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
        sim = {}
        for sim in self._balance:
            if sim.get("state") == "active":
                return sim
        return sim

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
    def gps_count(self):
        """GSM signal level."""
        return self._gps_count

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
    def phone(self):
        """Device phone number."""
        return self._phone

    @property
    def fuel_litres(self):
        """Device fuel count in litres."""
        return self._fuel_litres

    @property
    def fuel_percent(self):
        """Device fuel count in percent."""
        return self._fuel_percent

    @property
    def mileage(self):
        """Device mileage count."""
        return self._mileage
