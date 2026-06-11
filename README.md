# AlarmMonitor

Windows-Client zur Anzeige eines Alarmstatus aus Node-RED, Wetterdaten, Warnkarte, Uhrzeit und Logo.

## Schnellstart

1. Aktuelles Release-ZIP herunterladen.
2. ZIP in einen eigenen Ordner entpacken.
3. `config.json` anpassen, vor allem `alarm.server_url`.
4. `client_gui.exe` starten.

Diese Dateien muessen zusammen im selben Ordner liegen:

- `client_gui.exe`
- `updater.exe`
- `config.json`
- `alarm.wav`
- `Icon_oben_rechts.png`
- `version.txt`

## Updates

Die App prueft das neueste GitHub Release ueber:

- `https://github.com/Overdrive05/AlarmMonitor/releases/latest/download/version.txt`
- `https://github.com/Overdrive05/AlarmMonitor/releases/latest/download/client_gui.exe`

Damit der Update-Button funktioniert, muessen diese beiden Dateien bei jedem neuen GitHub Release als Assets hochgeladen werden.

## Konfiguration

Wichtige Werte in `config.json`:

- `alarm.server_url`: HTTP-Endpunkt des Alarmservers, z. B. `http://SERVER-IP:1880/alarm-status`
- `alarm.check_interval`: Abfrageintervall in Sekunden
- `weather.location_name`, `weather.latitude`, `weather.longitude`: Wetterstandort
- `map.image_url`: direkte Bild-URL der Karte
- `ui.crest_file`: Logo/Wappen oben rechts

Der Alarmserver muss JSON in dieser Form liefern:

```json
{
  "alarm": true,
  "text": "F 1",
  "timestamp": "2026-04-10T12:00:00Z"
}
```

## Build

Voraussetzungen:

- Python 3.13
- `requests`
- `customtkinter`
- `win10toast`
- `pillow`
- `pyinstaller`

Build-Befehle:

```powershell
pyinstaller --noconfirm --clean client_gui.spec
pyinstaller --noconfirm --clean updater.spec
```

Danach die benoetigten Begleitdateien in den Ausgabeordner kopieren.
