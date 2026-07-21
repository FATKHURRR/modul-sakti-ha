# Modul Sakti BMS Monitor (HACS Custom Integration)

Integrasi ini menggantikan cara lama (generate file YAML manual) dengan
Custom Component yang otomatis:

- Integrasi banyak **ID Modul** sekaligus (tambah/hapus kapan saja lewat Options)
- Auto-detect **BMS** (brand + address) yang terhubung ke tiap ID modul,
  tanpa perlu download/upload file YAML lagi
- Membuat entity untuk info modul (IP, RSSI, uptime, firmware) dan semua data
  BMS (voltage, current, power, SOC, SOH, capacity, cycle count, 15 cell voltage)

## Instalasi via HACS (Custom Repository)

1. HACS -> menu titik tiga (kanan atas) -> **Custom repositories**
2. Masukkan URL : https://github.com/FATKHURRR/modul-sakti-ha ,  kategori pilih **Integration**
3. Cari "Modul Sakti BMS Monitor" di HACS -> Download
4. Restart Home Assistant

## Instalasi Manual

Copy folder `custom_components/modul_sakti` ke folder `custom_components/`
milik Home Assistant kamu, lalu restart.

## Setup

1. Settings -> Devices & Services -> Add Integration -> cari **Modul Sakti**
2. Masukkan **ID Modul** pertama, lalu pilih **Server** dari dropdown (tidak perlu isi host/port/user/pass manual):
   - Server 1 -> `Modul Versi Baru`
   - Server 2 -> `Modul Versi Awal`
3. Setelah entry terbuat, klik **Configure** pada integrasi ini untuk:
   - **Tambah ID Modul** -> masukkan ID logger/modul + pilih server
   - **Hapus ID Modul** -> pilih dari daftar yang sudah ada
   - Tiap ID modul bebas pakai server yang berbeda-beda
4. Entity akan otomatis muncul:
   - Device "Modul Sakti `<id>` Info" -> IP, RSSI, Uptime, Firmware
   - Device "`<brand>#<addr>`" -> semua data BMS, muncul otomatis 

## Catatan

- Bisa campur: sebagian ID modul pakai Server 1, sebagian pakai Server 2,
  dalam satu integrasi yang sama.

