"""Dedicated MQTT client per broker preset (Server 1 / Server 2).

Satu ModulSaktiMqttClient = satu koneksi ke satu preset server. Kalau
module id yang terdaftar memakai server berbeda-beda, akan ada beberapa
instance client (satu per server yang benar-benar dipakai).
"""
from __future__ import annotations

import logging
import os
import re
import sys

# --- Pakai paho-mqtt yang di-vendor (dibundel langsung di folder ini),
# jadi tidak perlu pip install apa pun saat runtime. ---
_VENDOR_DIR = os.path.join(os.path.dirname(__file__), "vendor")
if _VENDOR_DIR not in sys.path:
    sys.path.insert(0, _VENDOR_DIR)

import paho.mqtt.client as mqtt  # noqa: E402  (harus setelah sys.path di atas)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    SIGNAL_BMS_UPDATE,
    SIGNAL_CONNECTION_STATUS,
    SIGNAL_INFO_UPDATE,
    SIGNAL_NEW_BMS,
)

_LOGGER = logging.getLogger(__name__)

# sysMon/<id>/AutoPoll/<brand>/<addr>
AUTOPOLL_RE = re.compile(r"^sysMon/([^/]+)/AutoPoll/([^/]+)/([^/]+)$")
# sysMon/<id>/info/  (trailing slash dari device asli, tapi juga terima tanpa slash)
INFO_RE = re.compile(r"^sysMon/([^/]+)/info/?$")


class ModulSaktiMqttClient:
    """Wrapper paho-mqtt untuk satu broker preset (server_1 / server_2)."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        server_key: str,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
    ) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.server_key = server_key
        self._host = host
        self._port = port
        self._module_ids: set[str] = set()
        # (module_id, brand, addr) yang sudah pernah terlihat -> untuk trigger "BMS baru"
        self._known_bms: set[tuple[str, str, str]] = set()

        client_id = f"ha_modul_sakti_{server_key}_{entry_id[:8]}"
        self._client = mqtt.Client(client_id=client_id, clean_session=True)
        if username:
            self._client.username_pw_set(username, password or None)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

    async def async_connect(self) -> None:
        await self.hass.async_add_executor_job(
            self._client.connect, self._host, self._port, 60
        )
        self._client.loop_start()

    async def async_disconnect(self) -> None:
        await self.hass.async_add_executor_job(self._client.loop_stop)
        await self.hass.async_add_executor_job(self._client.disconnect)

    # --- kelola daftar module id yang di-subscribe di server ini ---

    def subscribe_module(self, module_id: str) -> None:
        self._module_ids.add(module_id)
        if self._client.is_connected():
            self._client.subscribe(f"sysMon/{module_id}/#")

    def unsubscribe_module(self, module_id: str) -> None:
        self._module_ids.discard(module_id)
        if self._client.is_connected():
            self._client.unsubscribe(f"sysMon/{module_id}/#")

    @property
    def has_modules(self) -> bool:
        return bool(self._module_ids)

    # --- callback paho (jalan di thread paho, bukan event loop HA!) ---

    def _on_connect(self, client, userdata, flags, rc) -> None:
        if rc != 0:
            _LOGGER.error(
                "Modul Sakti [%s]: gagal konek ke %s:%s (rc=%s)",
                self.server_key,
                self._host,
                self._port,
                rc,
            )
            self.hass.loop.call_soon_threadsafe(
                async_dispatcher_send,
                self.hass,
                SIGNAL_CONNECTION_STATUS.format(
                    entry_id=self.entry_id, server=self.server_key
                ),
                False,
            )
            return

        _LOGGER.info(
            "Modul Sakti [%s]: terhubung ke broker %s:%s",
            self.server_key,
            self._host,
            self._port,
        )
        for module_id in self._module_ids:
            client.subscribe(f"sysMon/{module_id}/#")

        self.hass.loop.call_soon_threadsafe(
            async_dispatcher_send,
            self.hass,
            SIGNAL_CONNECTION_STATUS.format(
                entry_id=self.entry_id, server=self.server_key
            ),
            True,
        )

    def _on_disconnect(self, client, userdata, rc) -> None:
        _LOGGER.warning(
            "Modul Sakti [%s]: koneksi broker terputus (rc=%s)", self.server_key, rc
        )
        self.hass.loop.call_soon_threadsafe(
            async_dispatcher_send,
            self.hass,
            SIGNAL_CONNECTION_STATUS.format(
                entry_id=self.entry_id, server=self.server_key
            ),
            False,
        )

    def _on_message(self, client, userdata, msg) -> None:
        topic = msg.topic
        try:
            payload = msg.payload.decode("utf-8", errors="ignore")
        except Exception:  # noqa: BLE001
            return

        info_match = INFO_RE.match(topic)
        if info_match:
            module_id = info_match.group(1)
            self.hass.loop.call_soon_threadsafe(
                async_dispatcher_send,
                self.hass,
                SIGNAL_INFO_UPDATE.format(entry_id=self.entry_id, module_id=module_id),
                payload,
            )
            return

        auto_match = AUTOPOLL_RE.match(topic)
        if auto_match:
            module_id, brand, addr = auto_match.groups()
            key = (module_id, brand, addr)
            if key not in self._known_bms:
                self._known_bms.add(key)
                self.hass.loop.call_soon_threadsafe(
                    async_dispatcher_send,
                    self.hass,
                    SIGNAL_NEW_BMS.format(entry_id=self.entry_id),
                    module_id,
                    brand,
                    addr,
                )
            self.hass.loop.call_soon_threadsafe(
                async_dispatcher_send,
                self.hass,
                SIGNAL_BMS_UPDATE.format(
                    entry_id=self.entry_id, module_id=module_id, brand=brand, addr=addr
                ),
                payload,
            )
