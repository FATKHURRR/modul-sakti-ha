"""The Modul Sakti BMS Monitor integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant

from .const import (
    BROKER_PRESETS,
    CONF_MODULE_ID,
    CONF_SERVER,
    DOMAIN,
)
from .mqtt_client import ModulSaktiMqttClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up Modul Sakti."""

    module_id = entry.data[CONF_MODULE_ID]

    server = entry.options.get(
        CONF_SERVER,
        next(iter(BROKER_PRESETS)),
    )

    preset = BROKER_PRESETS[server]

    client = ModulSaktiMqttClient(
        hass=hass,
        entry_id=entry.entry_id,
        server_key=server,
        host=preset[CONF_HOST],
        port=preset[CONF_PORT],
        username=preset[CONF_USERNAME],
        password=preset[CONF_PASSWORD],
    )

    client.subscribe_module(module_id)

    await client.async_connect()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = client

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    entry.async_on_unload(
        entry.add_update_listener(_async_update_listener)
    )

    return True


async def _async_update_listener(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Reload config ketika options berubah."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload Modul Sakti."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        client: ModulSaktiMqttClient = hass.data[DOMAIN].pop(
            entry.entry_id
        )

        await client.async_disconnect()

    return unload_ok