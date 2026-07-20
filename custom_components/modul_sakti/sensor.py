"""Sensor platform for Modul Sakti BMS Monitor."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_MODULE_ID,
    DOMAIN,
    MANUFACTURER,
    SIGNAL_BMS_UPDATE,
    SIGNAL_INFO_UPDATE,
    SIGNAL_NEW_BMS,
)

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Info sensors (topic: sysMon/<id>/info/  -> payload CSV)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class InfoSensorDescription(SensorEntityDescription):
    csv_index: int = 0
    value_fn: Callable[[str], Any] = lambda raw: raw


def _parse_uptime(raw: str) -> str | None:
    try:
        seconds = int(float(raw))
    except (ValueError, TypeError):
        return None
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


INFO_SENSOR_DESCRIPTIONS: tuple[InfoSensorDescription, ...] = (
    InfoSensorDescription(
        key="ip",
        name="IP Address",
        icon="mdi:ip-network",
        csv_index=0,
        value_fn=lambda raw: raw,
    ),
    InfoSensorDescription(
        key="rssi",
        name="RSSI",
        native_unit_of_measurement="dBm",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        csv_index=1,
        value_fn=lambda raw: int(float(raw)),
    ),
    InfoSensorDescription(
        key="uptime",
        name="Uptime",
        icon="mdi:timer-outline",
        csv_index=2,
        value_fn=_parse_uptime,
    ),
    InfoSensorDescription(
        key="firmware",
        name="Firmware Version",
        icon="mdi:firmware",
        csv_index=11,
        value_fn=lambda raw: raw,
    ),
)


class ModulSaktiInfoSensor(SensorEntity):
    """Sensor info modul (ip, rssi, uptime, firmware)."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self, entry_id: str, module_id: str, description: InfoSensorDescription
    ) -> None:
        self.entity_description = description
        self._entry_id = entry_id
        self._module_id = module_id
        self._attr_unique_id = f"{DOMAIN}_{module_id}_info_{description.key}"
        self._attr_available = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{module_id}_info")},
            name=f"Modul Sakti Info",
            manufacturer=MANUFACTURER,
            model="BMS Monitor",
        )

    async def async_added_to_hass(self) -> None:
        signal = SIGNAL_INFO_UPDATE.format(
            entry_id=self._entry_id, module_id=self._module_id
        )
        self.async_on_remove(
            async_dispatcher_connect(self.hass, signal, self._handle_payload)
        )

    @callback
    def _handle_payload(self, payload: str) -> None:
        parts = payload.split(",")
        idx = self.entity_description.csv_index
        if idx >= len(parts):
            return
        try:
            self._attr_native_value = self.entity_description.value_fn(parts[idx])
        except (ValueError, TypeError, IndexError):
            return
        self._attr_available = True
        self.async_write_ha_state()


# ---------------------------------------------------------------------------
# BMS sensors (topic: sysMon/<id>/AutoPoll/<brand>/<addr> -> payload JSON)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BmsSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict], Any] = field(default=lambda data: None)


def _cell_value_fn(index: int) -> Callable[[dict], Any]:
    def _fn(data: dict) -> float | None:
        try:
            cells = data.get("cell_voltages") or []
            return round(float(cells[index]) / 1000, 3)
        except (IndexError, ValueError, TypeError):
            return None

    return _fn


BMS_SENSOR_DESCRIPTIONS: tuple[BmsSensorDescription, ...] = (
    BmsSensorDescription(
        key="bat_voltage",
        name="Voltage",
        native_unit_of_measurement="V",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda d: round(float(d.get("bat_voltage", 0)), 2),
    ),
    BmsSensorDescription(
        key="bus_voltage",
        name="Bus Voltage",
        native_unit_of_measurement="V",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda d: round(float(d.get("bus_voltage", 0)), 2),
    ),
    BmsSensorDescription(
        key="bat_current",
        name="Current",
        native_unit_of_measurement="A",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda d: round(float(d.get("bat_current", 0)), 2),
    ),
    BmsSensorDescription(
        key="bus_current",
        name="Bus Current",
        native_unit_of_measurement="A",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda d: round(float(d.get("bus_current", 0)), 2),
    ),
    BmsSensorDescription(
        key="pack_power",
        name="Pack Power",
        native_unit_of_measurement="W",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda d: round(
            float(d.get("bat_current", 0)) * float(d.get("bat_voltage", 0)), 2
        ),
    ),
    BmsSensorDescription(
        key="bus_power",
        name="Bus Power",
        native_unit_of_measurement="W",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda d: round(
            float(d.get("bus_current", 0)) * float(d.get("bus_voltage", 0)), 2
        ),
    ),
    BmsSensorDescription(
        key="soc",
        name="SOC",
        native_unit_of_measurement="%",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda d: round(float(d.get("SOC", 0)), 1),
    ),
    BmsSensorDescription(
        key="soh",
        name="SOH",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:heart-pulse",
        value_fn=lambda d: round(float(d.get("SOH", 0)), 1),
    ),
    BmsSensorDescription(
        key="full_capacity",
        name="Full Capacity",
        native_unit_of_measurement="Ah",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-high",
        value_fn=lambda d: float(d.get("full_capacity", 0)),
    ),
    BmsSensorDescription(
        key="rem_capacity",
        name="Remaining Capacity",
        native_unit_of_measurement="Ah",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-50",
        value_fn=lambda d: float(d.get("rem_capacity", 0)),
    ),
    BmsSensorDescription(
        key="cycle_count",
        name="Cycle Count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-sync",
        value_fn=lambda d: int(d.get("cycle_count", 0)),
    ),
    BmsSensorDescription(
        key="cell_vmax",
        name="Cell Voltage Max",
        native_unit_of_measurement="V",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        value_fn=lambda d: round(float(d.get("cell_vmax", 0)) / 1000, 3),
    ),
    BmsSensorDescription(
        key="cell_vmin",
        name="Cell Voltage Min",
        native_unit_of_measurement="V",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        value_fn=lambda d: round(float(d.get("cell_vmin", 0)) / 1000, 3),
    ),
    BmsSensorDescription(
        key="cell_vdiff",
        name="Cell Voltage Diff",
        native_unit_of_measurement="V",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        value_fn=lambda d: round(float(d.get("cell_vdiff", 0)) / 1000, 3),
    ),
) + tuple(
    BmsSensorDescription(
        key=f"cell_{i:02d}",
        name=f"Cell {i} Voltage",
        native_unit_of_measurement="V",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        value_fn=_cell_value_fn(i - 1),
    )
    for i in range(1, 16)
)


class ModulSaktiBmsSensor(SensorEntity):
    """Sensor satu titik data BMS (satu brand+addr per module id)."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        entry_id: str,
        module_id: str,
        brand: str,
        addr: str,
        description: BmsSensorDescription,
    ) -> None:
        self.entity_description = description
        self._entry_id = entry_id
        self._module_id = module_id
        self._brand = brand
        self._addr = addr
        lower_brand = brand.lower()
        self._attr_unique_id = (
            f"{lower_brand}_{module_id}_bat{addr}_{description.key}"
        )
        self._attr_available = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{lower_brand}_{module_id}_bat{addr}")},
            name=f"{brand}#{addr}",
            manufacturer=MANUFACTURER,
            model=f"Modul Sakti - {brand}",
        )

    async def async_added_to_hass(self) -> None:
        signal = SIGNAL_BMS_UPDATE.format(
            entry_id=self._entry_id,
            module_id=self._module_id,
            brand=self._brand,
            addr=self._addr,
        )
        self.async_on_remove(
            async_dispatcher_connect(self.hass, signal, self._handle_payload)
        )

    @callback
    def _handle_payload(self, payload: str) -> None:
        try:
            data = json.loads(payload)
        except (ValueError, TypeError):
            return
        try:
            value = self.entity_description.value_fn(data)
        except (KeyError, ValueError, TypeError):
            return
        if value is None:
            return
        self._attr_native_value = value
        self._attr_available = True
        self.async_write_ha_state()


# ---------------------------------------------------------------------------
# Platform setup (Fixed setup entry context)
# ---------------------------------------------------------------------------

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Modul Sakti sensor platform."""
    module_id = entry.data[CONF_MODULE_ID]

    # 1. Setup sensor static bawaan modul (Info sensor)
    info_entities = [
        ModulSaktiInfoSensor(
            entry.entry_id,
            module_id,
            description,
        )
        for description in INFO_SENSOR_DESCRIPTIONS
    ]
    async_add_entities(info_entities)

    # 2. Setup listener dinamis untuk penemuan AutoPoll BMS baru
    @callback
    def _handle_new_bms(new_module_id: str, brand: str, addr: str) -> None:
        if new_module_id != module_id:
            return

        _LOGGER.info(
            "BMS baru ditemukan secara otomatis: %s %s %s",
            new_module_id,
            brand,
            addr,
        )

        bms_entities = [
            ModulSaktiBmsSensor(
                entry.entry_id,
                new_module_id,
                brand,
                addr,
                description,
            )
            for description in BMS_SENSOR_DESCRIPTIONS
        ]
        async_add_entities(bms_entities)

    # Hubungkan dispatcher dan daftarkan ke unload tracker milik entry agar tidak memory leak
    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            SIGNAL_NEW_BMS.format(entry_id=entry.entry_id),
            _handle_new_bms,
        )
    )