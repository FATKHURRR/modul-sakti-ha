"""Validasi ID modul terhadap daftar ID yang diizinkan (Google Sheet CSV)."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import ALLOWED_IDS_CSV_URL

_LOGGER = logging.getLogger(__name__)


async def async_is_id_allowed(hass: HomeAssistant, module_id: str) -> bool:
    """Cek apakah module_id ada di dalam daftar ID yang diizinkan.

    CSV di-fetch langsung (tidak di-cache) supaya user selalu dicek
    terhadap daftar terbaru. Sheet-nya kecil (~300 baris) jadi ringan.

    Fail-open: kalau sheet gagal diambil (jaringan/CSV bermasalah),
    validasi dilewati (return True) supaya user tidak terblokir gara-gara
    masalah di luar kendali mereka -- hanya di-log sebagai warning. Ubah
    baris "return True" di except/if di bawah jadi "return False" kalau
    mau perilaku fail-closed (lebih ketat, tapi user bisa tertolak saat
    sheet down).
    """
    session = async_get_clientsession(hass)
    try:
        async with session.get(ALLOWED_IDS_CSV_URL, timeout=10) as resp:
            if resp.status != 200:
                _LOGGER.warning(
                    "Gagal ambil daftar ID yang diizinkan (HTTP %s), "
                    "validasi ID dilewati",
                    resp.status,
                )
                return True
            text = await resp.text()
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning(
            "Gagal ambil daftar ID yang diizinkan (%s), validasi ID dilewati",
            err,
        )
        return True

    allowed = {line.strip() for line in text.splitlines() if line.strip()}
    return module_id in allowed
