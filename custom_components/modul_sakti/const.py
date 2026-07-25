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

# Google Sheet (publish to web, CSV) berisi daftar ID modul yang diizinkan.
# Format: satu kolom, satu ID per baris, tanpa header.
ALLOWED_IDS_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vRxTJX1kVRG50_XxNu1afGm67MgJ_0Pkydv0de-_vYKqZvjtjYVtWi0H_CJnA-JcRxq94sKWnfvajfi/"
    "pub?gid=948299467&single=true&output=csv"
)

# Dispatcher signal templates (di-format dengan .format(...) sebelum dipakai)
SIGNAL_INFO_UPDATE = "modul_sakti_info_{entry_id}_{module_id}"
SIGNAL_INFOJSON_UPDATE = "modul_sakti_infojson_{entry_id}_{module_id}"
SIGNAL_NEW_INFOJSON = "modul_sakti_new_infojson_{entry_id}"
SIGNAL_BMS_UPDATE = "modul_sakti_bms_{entry_id}_{module_id}_{brand}_{addr}"
SIGNAL_NEW_BMS = "modul_sakti_new_bms_{entry_id}"
SIGNAL_CONNECTION_STATUS = "modul_sakti_conn_{entry_id}_{server}"
