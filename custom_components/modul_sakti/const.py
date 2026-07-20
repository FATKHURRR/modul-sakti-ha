"""Constants for the Modul Sakti integration."""

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME

DOMAIN = "modul_sakti"
MANUFACTURER = "Modul Sakti"

# Setiap module id menyimpan dict: {"id": <module_id>, "server": <preset key>}
CONF_MODULES = "modules"
CONF_MODULE_ID = "module_id"
CONF_SERVER = "server"

# Preset broker -- user tinggal pilih, tidak perlu input manual
BROKER_PRESETS: dict[str, dict] = {
    "server_1": {
        "label": "Server 1 ",
        CONF_HOST: "broker.emqx.io",
        CONF_PORT: 1883,
        CONF_USERNAME: "emqx",
        CONF_PASSWORD: "emqx",
    },
    "server_2": {
        "label": "Server 2 ",
        CONF_HOST: "public.cloud.shiftr.io",
        CONF_PORT: 1883,
        CONF_USERNAME: "public",
        CONF_PASSWORD: "public",
    },
}

# Dispatcher signal templates (di-format dengan .format(...) sebelum dipakai)
SIGNAL_INFO_UPDATE = "modul_sakti_info_{entry_id}_{module_id}"
SIGNAL_BMS_UPDATE = "modul_sakti_bms_{entry_id}_{module_id}_{brand}_{addr}"
SIGNAL_NEW_BMS = "modul_sakti_new_bms_{entry_id}"
SIGNAL_CONNECTION_STATUS = "modul_sakti_conn_{entry_id}_{server}"
