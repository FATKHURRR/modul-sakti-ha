"""Config flow for Modul Sakti BMS Monitor.

Satu config entry = satu ID modul. Untuk menambah ID modul lain, user
tinggal klik "Add Integration" -> "Modul Sakti" lagi (bukan lewat Options).
Options ("Configure") dipakai hanya untuk ganti server broker ID ini.
"""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import BROKER_PRESETS, CONF_MODULE_ID, CONF_SERVER, DOMAIN


def _server_selector() -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=key, label=preset["label"])
                for key, preset in BROKER_PRESETS.items()
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )



def _module_schema(default_server: str | None = None) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_MODULE_ID): str,
            vol.Required(CONF_SERVER, default=default_server): _server_selector(),
        }
    )


class ModulSaktiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow untuk satu ID Modul Sakti."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            module_id = str(user_input[CONF_MODULE_ID]).strip()
            if not module_id:
                errors["base"] = "invalid_id"
            else:
                await self.async_set_unique_id(module_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Modul Sakti - {module_id}",
                    data={CONF_MODULE_ID: module_id},
                    options={CONF_SERVER: user_input[CONF_SERVER]},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_MODULE_ID): str,
                vol.Required(CONF_SERVER): _server_selector(),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> ModulSaktiOptionsFlow:
        return ModulSaktiOptionsFlow()


class ModulSaktiOptionsFlow(config_entries.OptionsFlow):
    """Options flow: ganti server broker untuk ID modul ini.

    Tidak override __init__ / tidak menyimpan self.config_entry secara
    manual -- versi HA terbaru sudah menyediakan self.config_entry secara
    otomatis, dan menimpanya manual menyebabkan error 500 saat flow dibuka.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        current_server = self.config_entry.options.get(
            CONF_SERVER, next(iter(BROKER_PRESETS))
        )

        if user_input is not None:
            return self.async_create_entry(
                title="", data={CONF_SERVER: user_input[CONF_SERVER]}
            )

        schema = vol.Schema(
            {vol.Required(CONF_SERVER, default=current_server): _server_selector()}
        )
        return self.async_show_form(step_id="init", data_schema=schema)



