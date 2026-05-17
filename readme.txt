ALARM MONITOR – CLIENT

==================================================
1. ZWECK DES PROGRAMMS
==================================================

Dieses Programm zeigt folgende Informationen an:

- Alarmstatus vom Alarmserver
- Wetterdaten für einen frei wählbaren Standort
- Kartenansicht
- Wappen / Logo oben rechts

Das Programm wird über die Datei "client_gui.exe" gestartet.
Die Einstellungen werden über die Datei "config.json" vorgenommen.

==================================================
2. ERFORDERLICHE DATEIEN
==================================================

Damit das Programm funktioniert, müssen sich ALLE folgenden Dateien
im selben Ordner befinden:

- client_gui.exe
- config.json
- Icon_oben_rechts.png
- alarm.wav

Wichtig:
Es dürfen keine Dateien fehlen.
Die Dateien dürfen nicht in Unterordner verschoben werden.

Beispiel:

AlarmMonitor_Paket\
    client_gui.exe
    config.json
    Icon_oben_rechts.png
    alarm.wav
    README.txt

==================================================
3. PROGRAMM STARTEN
==================================================

Das Programm wird gestartet durch Doppelklick auf:

client_gui.exe

==================================================
4. KONFIGURATION
==================================================

Alle Einstellungen werden in der Datei "config.json" vorgenommen.

Die Datei muss mit einem Texteditor bearbeitet werden, zum Beispiel:

- Editor
- Notepad++
- Visual Studio Code

Wichtig:
Die Datei muss nach Änderungen wieder als "config.json" gespeichert werden.
Der Dateiname darf nicht geändert werden.

==================================================
5. SERVER EINSTELLEN
==================================================

In der Datei "config.json" gibt es folgenden Bereich:

"alarm": {
  "server_url": "http://IHRE IP-ADRESSE:1880/alarm-status",
  "check_interval": 3,
  "sound_enabled": true,
  "monitoring_enabled": true,
  "sound_file": "alarm.wav"
}

Geändert werden muss bei Bedarf:

"server_url"

Beispiel:

"server_url": "http://123.456.7.89:1234/Beispiel"

Bedeutung:
- 123.456.7.89 = IP-Adresse des Alarmservers
- 1234 = Port
- /Beispiel = Pfad zum Endpunkt

Nur die tatsächlichen Daten des eigenen Servers eintragen.
Die URL muss vollständig und korrekt eingetragen werden.

==================================================
6. WETTER STANDORT RICHTIG ÄNDERN
==================================================

WICHTIG:
Für den Wetter-Standort müssen IMMER sowohl der Ortsname
ALS AUCH die Koordinaten angepasst werden.

Es reicht ausdrücklich NICHT aus, nur den Ortsnamen zu ändern.

In der Datei "config.json" gibt es folgenden Bereich:

"weather": {
  "location_name": "Raunheim",
  "use_coordinates_directly": false,
  "latitude": 50.0136,
  "longitude": 8.4519,
  "timezone": "Europe/Berlin",
  "update_interval": 600
}

Folgende drei Werte müssen gemeinsam geändert werden:

1. "location_name"
2. "latitude"
3. "longitude"

Beispiel für Frankfurt am Main:

"weather": {
  "location_name": "Frankfurt am Main",
  "use_coordinates_directly": false,
  "latitude": 50.1109,
  "longitude": 8.6821,
  "timezone": "Europe/Berlin",
  "update_interval": 600
}

Vorgehensweise ohne Fehler:

1. Gewünschten Ort festlegen
2. Exakten Ortsnamen eintragen bei:
   "location_name"
3. Die passenden Koordinaten dieses Ortes ermitteln
4. Breitengrad eintragen bei:
   "latitude"
5. Längengrad eintragen bei:
   "longitude"
6. Datei speichern
7. Programm neu starten

Wichtig:
Wenn Ortsname und Koordinaten nicht zusammenpassen,
kann es zu falschen Wetterdaten kommen.

==================================================
7. KARTENDATEN ÄNDERN
==================================================

In der Datei "config.json" gibt es folgenden Bereich:

"map": {
  "image_url": "https://www.dwd.de/DWD/warnungen/warnapp_gemeinden/json/warnungen_gemeinde_map_hes.png",
  "update_interval": 600,
  "max_width": 900,
  "max_height": 650
}

Geändert werden kann bei Bedarf:

"image_url"

Hier muss die vollständige Bild-URL der gewünschten Karte eingetragen werden.

Wichtig:
Die URL muss direkt auf eine Bilddatei verweisen, damit die Karte geladen werden kann.

==================================================
8. WAPPEN / LOGO OBEN RECHTS
==================================================

Die Datei für das Wappen / Logo oben rechts muss heißen:

Icon_oben_rechts.png

Erforderlicher Dateityp:
PNG

Die Datei MUSS also eine PNG-Datei sein.

Nicht verwenden:
- JPG
- JPEG
- BMP
- WEBP
- ICO

Wenn ein anderes Bild verwendet werden soll, muss es zuerst in das
PNG-Format umgewandelt werden.

Wichtig:
Standardmäßig erwartet das Programm genau diese Datei:

Icon_oben_rechts.png

Wenn der Dateiname geändert werden soll, muss in der "config.json"
ebenfalls der Eintrag angepasst werden:

"crest_file": "Icon_oben_rechts.png"

==================================================
9. ALARMTON
==================================================

Die Alarmton-Datei muss heißen:

alarm.wav

Erforderlicher Dateityp:
WAV

Die Datei MUSS also eine WAV-Datei sein.

Nicht verwenden:
- MP3
- WMA
- AAC
- OGG

Wenn ein anderer Alarmton verwendet werden soll, muss er zuerst in
das WAV-Format umgewandelt werden.

Wichtig:
Standardmäßig erwartet das Programm genau diese Datei:

alarm.wav

Wenn der Dateiname geändert werden soll, muss in der "config.json"
ebenfalls der Eintrag angepasst werden:

"sound_file": "alarm.wav"

==================================================
10. AUTOSTART EINRICHTEN (OPTIONAL)
==================================================

Wenn das Programm automatisch beim Windows-Start ausgeführt werden soll,
kann die EXE in den Autostart eingetragen werden.

Empfohlene Vorgehensweise:

1. Tastenkombination drücken:
   Windows-Taste + R

2. In das Feld eingeben:
   shell:startup

3. Mit Enter bestätigen

4. Es öffnet sich der Windows-Autostart-Ordner

5. In diesen Ordner eine Verknüpfung von "client_gui.exe" einfügen

Wichtig:
Nicht die EXE verschieben, sondern eine VERKNÜPFUNG anlegen.

Vorgehensweise:

- Rechtsklick auf client_gui.exe
- "Senden an"
- "Desktop (Verknüpfung erstellen)"
- die erstellte Verknüpfung vom Desktop in den Autostart-Ordner ziehen

Hinweis:
Die Originaldateien müssen weiterhin vollständig im ursprünglichen Ordner liegen:

- client_gui.exe
- config.json
- Icon_oben_rechts.png
- alarm.wav

Wenn die EXE ohne die Begleitdateien verschoben wird, funktioniert das
Programm nicht korrekt.

==================================================
11. WICHTIGE HINWEISE ZUR FEHLERVERMEIDUNG
==================================================

- Alle Dateien müssen im selben Ordner liegen
- Die Datei "config.json" muss korrekt formatiert sein
- Ortsname UND Koordinaten müssen immer gemeinsam angepasst werden
- Das Wappen oben rechts muss eine PNG-Datei sein
- Der Alarmton muss eine WAV-Datei sein
- Die EXE darf nicht ohne die Begleitdateien verschoben werden
- Nach Änderungen an der "config.json" das Programm neu starten

==================================================
12. FEHLERBEHEBUNG
==================================================

"Wappen nicht gefunden"
Ursache:
- Datei fehlt
- Dateiname falsch
- falscher Dateityp

Prüfung:
- Liegt "Icon_oben_rechts.png" im selben Ordner wie die EXE?
- Ist es wirklich eine PNG-Datei?
- Ist der Dateiname exakt richtig geschrieben?

"Server nicht erreichbar"
Ursache:
- falsche IP-Adresse
- falscher Port
- Server läuft nicht
- Netzwerkproblem
- Firewall blockiert den Zugriff

Prüfung:
- Eintrag "server_url" in der config.json kontrollieren
- Erreichbarkeit des Servers prüfen
- Netzwerkverbindung prüfen

"Status unbekannt"
Ursache:
- Verbindung zum Alarmserver fehlgeschlagen
- Server liefert keine gültigen Daten

"Wetter nicht verfügbar"
Ursache:
- keine Internetverbindung
- fehlerhafte Standortdaten
- Ortsname und Koordinaten passen nicht zusammen

Prüfung:
- "location_name" prüfen
- "latitude" prüfen
- "longitude" prüfen

==================================================
13. SUPPORT
==================================================

Bei Fehlern oder Rückfragen wenden Sie sich bitte an:

t.schneider@feuerwehr-raunheim.de

==================================================
ENDE
==================================================