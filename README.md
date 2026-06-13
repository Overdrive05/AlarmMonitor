# AlarmMonitor

Moderner Windows-Client zur Anzeige eines Alarmstatus aus Node-RED, Wetterdaten, Warnkarte, Uhrzeit und Logo.

Die App ist als fertiges Release-Paket nutzbar. Nutzer muessen keinen Python-Code ausfuehren.

## Schnellstart

1. Auf der GitHub-Seite unter **Releases** das aktuelle `AlarmMonitor_*.zip` herunterladen.
2. ZIP in einen eigenen Ordner entpacken.
3. `config.json` mit einem Texteditor anpassen.
4. `client_gui.exe` starten.

Diese Dateien muessen zusammen im selben Ordner liegen:

- `client_gui.exe`
- `updater.exe`
- `config.json`
- `alarm.wav`
- `Icon_oben_rechts.png`
- `version.txt`

## Anpassen

Alle normalen Anpassungen passieren in `config.json`.

### Alarmserver

```json
"alarm": {
  "server_url": "http://SERVER-IP:1880/alarm-status",
  "check_interval": 3,
  "sound_enabled": true,
  "monitoring_enabled": true,
  "sound_file": "alarm.wav"
}
```

`server_url` muss auf den eigenen Node-RED-Endpunkt zeigen.

### Wetter

```json
"weather": {
  "location_name": "Raunheim",
  "use_coordinates_directly": false,
  "latitude": 50.0136,
  "longitude": 8.4519,
  "timezone": "Europe/Berlin",
  "update_interval": 600
}
```

Bei einem anderen Ort am besten `location_name`, `latitude` und `longitude` gemeinsam anpassen.

### Karte

```json
"map": {
  "image_url": "https://www.dwd.de/DWD/warnungen/warnapp_gemeinden/json/warnungen_gemeinde_map_hes.png",
  "update_interval": 600,
  "max_width": 900,
  "max_height": 650
}
```

`image_url` muss direkt auf eine Bilddatei zeigen.

### Design

```json
"ui": {
  "appearance_mode": "dark",
  "color_theme": "blue",
  "crest_file": "Icon_oben_rechts.png",
  "clock_font_family": "Arial",
  "station_name": "Feuerwehr Raunheim",
  "map_title": "Warnkarte",
  "accent_color": "#2f81f7",
  "normal_color": "#2fbf71",
  "alarm_color": "#ff4d4f",
  "warning_color": "#f5a524",
  "background_color": "#07111f",
  "panel_color": "#101b2b",
  "panel_alt_color": "#142235",
  "muted_text_color": "#94a3b8",
  "primary_text_color": "#f8fafc"
}
```

Wichtige Werte:

- `station_name`: Name der Einheit oder Organisation in der Kopfzeile
- `map_title`: Titel der Kartenflaeche
- `crest_file`: PNG-Datei fuer das Logo/Wappen
- `clock_font_family`: Schriftart fuer Uhr und UI
- `normal_color`: Farbe fuer Normalzustand
- `alarm_color`: Farbe fuer Alarmzustand
- `background_color`, `panel_color`, `panel_alt_color`: Grundfarben des modernen Designs

## Node-RED-Endpunkt

Der Alarmserver muss JSON in dieser Form liefern:

```json
{
  "alarm": true,
  "text": "F 1",
  "timestamp": "2026-04-10T12:00:00Z"
}
```

Wenn kein Alarm aktiv ist:

```json
{
  "alarm": false,
  "text": "",
  "timestamp": ""
}
```

## Updates

Die App prueft das neueste GitHub Release ueber:

- `https://github.com/Overdrive05/AlarmMonitor/releases/latest/download/version.txt`
- `https://github.com/Overdrive05/AlarmMonitor/releases/latest/download/client_gui.exe`
- `https://github.com/Overdrive05/AlarmMonitor/releases/latest/download/updater.exe`

Damit der Update-Button funktioniert, muessen bei jedem Release mindestens diese Assets hochgeladen werden:

- `version.txt`
- `client_gui.exe`
- `updater.exe`

Fuer Neuinstallationen sollte zusaetzlich ein komplettes ZIP-Paket hochgeladen werden.

Der Update-Button ist der empfohlene Weg. Die App laedt dabei zuerst den neuesten
`updater.exe`, beendet sich selbst und der Updater ersetzt danach die vorhandene
`client_gui.exe`.

Wenn `updater.exe` manuell gestartet wird, sollte `client_gui.exe` vorher komplett
geschlossen sein. Ab Version `1.0.9` wartet der Updater laenger auf das Schliessen
der App, entfernt alte temporaere Dateien wie `client_gui_new.exe` und laesst bei
einem fehlgeschlagenen Update keine zweite Startdatei neben der eigentlichen App
liegen.

## Hinweis zu Virenscannern

Die EXE-Dateien werden mit PyInstaller gebaut und sind nicht code-signiert. Einige Virenscanner koennen neue oder selten heruntergeladene EXE-Dateien deshalb als unbekannt oder verdaechtig markieren. Lade die App nur aus dem offiziellen GitHub Release herunter und vergleiche bei Bedarf die SHA256-Hashes aus dem Release.

## Build aus dem Sourcecode

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

Danach die benoetigten Begleitdateien in den Ausgabeordner kopieren:

- `config.json`
- `alarm.wav`
- `Icon_oben_rechts.png`
- `version.txt`
