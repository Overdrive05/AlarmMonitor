import sys
import json
import os
import threading
import time
from datetime import datetime
from io import BytesIO
import subprocess


import requests
import winsound
import customtkinter as ctk
from win10toast import ToastNotifier
from PIL import Image

APP_VERSION = "1.0.5"

VERSION_URL = "https://github.com/Overdrive05/AlarmMonitor/releases/latest/download/version.txt"
UPDATER_URL = "https://github.com/Overdrive05/AlarmMonitor/releases/latest/download/updater.exe"

def get_base_path():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_resource_path(filename):
    return os.path.join(get_base_path(), filename)


def merge_config(default, custom):
    if not isinstance(custom, dict):
        return default

    merged = default.copy()

    for key, value in custom.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_config(merged[key], value)
        else:
            merged[key] = value

    return merged


def load_config(config_file="config.json"):
    config_path = os.path.join(get_base_path(), config_file)

    default_config = {
        "app_title": "Alarm Monitor",
        "alarm": {
            "server_url": "http://127.0.0.1:1880/alarm-status",
            "check_interval": 3,
            "sound_enabled": True,
            "monitoring_enabled": True,
            "sound_file": "alarm.wav"
        },
        "weather": {
            "location_name": "Raunheim",
            "use_coordinates_directly": False,
            "latitude": 50.0136,
            "longitude": 8.4519,
            "timezone": "Europe/Berlin",
            "update_interval": 600
        },
        "map": {
            "image_url": "https://www.dwd.de/DWD/warnungen/warnapp_gemeinden/json/warnungen_gemeinde_map_hes.png",
            "update_interval": 600,
            "max_width": 900,
            "max_height": 650
        },
        "ui": {
            "appearance_mode": "dark",
            "color_theme": "blue",
            "crest_file": "Icon_oben_rechts.png",
            "clock_font_family": "Arial"
        }
    }

    if not os.path.exists(config_path):
        print(f"Config nicht gefunden, Standardwerte werden verwendet: {config_path}")
        return default_config

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = json.load(f)
    except Exception as e:
        print(f"Fehler beim Laden der Config, Standardwerte werden verwendet: {e}")
        return default_config

    return merge_config(default_config, user_config)

CONFIG = load_config()

APP_TITLE = CONFIG["app_title"]

ALARM_CONFIG = CONFIG["alarm"]
WEATHER_CONFIG = CONFIG["weather"]
MAP_CONFIG = CONFIG["map"]
UI_CONFIG = CONFIG["ui"]

URL = ALARM_CONFIG["server_url"]
CHECK_INTERVAL = ALARM_CONFIG["check_interval"]
WEATHER_INTERVAL = WEATHER_CONFIG["update_interval"]
MAP_INTERVAL = MAP_CONFIG["update_interval"]

SOUND_ENABLED = ALARM_CONFIG["sound_enabled"]
MONITORING_ENABLED = ALARM_CONFIG["monitoring_enabled"]
last_alarm = False

toaster = ToastNotifier()


def play_alarm():
    try:
        sound_file = get_resource_path(ALARM_CONFIG["sound_file"])
        winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception as e:
        print("Sound Fehler:", e)


def show_notification():
    try:
        toaster.show_toast(
            "Einsatz",
            "Achtung Einsatz!",
            duration=5,
            threaded=False
        )
    except Exception as e:
        print("Notification Fehler:", e)


def parse_version(version):
    try:
        return tuple(int(part) for part in version.lstrip("v").split("."))
    except ValueError:
        return ()


def apply_update_state(online_version=None, error=None):
    if error:
        update_button.configure(
            text="Update prüfen",
            state="normal",
            command=check_for_update
        )
        print("Update prüfen Fehler:", error)
        return

    online_parsed = parse_version(online_version)
    local_parsed = parse_version(APP_VERSION)

    if not online_parsed or not local_parsed:
        update_button.configure(
            text="Update prüfen",
            state="normal",
            command=check_for_update
        )
        print("Update prüfen Fehler: ungültige Versionsnummer")
        return

    if online_parsed > local_parsed:
        update_button.configure(
            text=f"Update {online_version}",
            state="normal",
            command=start_update
        )
    else:
        update_button.configure(text="Aktuell", state="disabled")


def check_for_update():
    update_button.configure(text="Prüfe...", state="disabled")

    def worker():
        try:
            response = requests.get(VERSION_URL, timeout=10)
            response.raise_for_status()
            online_version = response.text.strip()
            app.after(0, lambda version=online_version: apply_update_state(online_version=version))
        except Exception as e:
            app.after(0, lambda error=e: apply_update_state(error=error))

    threading.Thread(target=worker, daemon=True).start()


def refresh_updater(updater_path):
    temp_path = updater_path + ".new"

    try:
        response = requests.get(UPDATER_URL, timeout=30)
        response.raise_for_status()

        with open(temp_path, "wb") as f:
            f.write(response.content)

        if os.path.getsize(temp_path) < 1_000_000:
            raise RuntimeError("Heruntergeladener Updater ist unerwartet klein.")

        with open(temp_path, "rb") as f:
            if f.read(2) != b"MZ":
                raise RuntimeError("Heruntergeladener Updater ist keine Windows-EXE.")

        os.replace(temp_path, updater_path)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)

        print("Updater aktualisieren Fehler:", e)


def start_update():
    try:
        updater_path = get_resource_path("updater.exe")

        update_button.configure(text="Update läuft...", state="disabled")
        app.update_idletasks()

        refresh_updater(updater_path)

        if not os.path.exists(updater_path):
            update_button.configure(
                text="Updater fehlt",
                state="normal",
                command=check_for_update
            )
            print("Update Fehler: updater.exe nicht gefunden")
            return

        subprocess.Popen([updater_path], cwd=get_base_path())
        app.destroy()
    except Exception as e:
        update_button.configure(
            text="Update Fehler",
            state="normal",
            command=check_for_update
        )
        print("Update Fehler:", e)

def toggle_sound():
    global SOUND_ENABLED
    SOUND_ENABLED = not SOUND_ENABLED
    sound_button.configure(text=f"Ton: {'AN' if SOUND_ENABLED else 'AUS'}")


def toggle_monitoring():
    global MONITORING_ENABLED
    MONITORING_ENABLED = not MONITORING_ENABLED
    monitoring_button.configure(text=f"Überwachung: {'AN' if MONITORING_ENABLED else 'AUS'}")


def update_clock():
    now = datetime.now()
    time_label.configure(text=now.strftime("%H:%M:%S"))
    date_label.configure(text=now.strftime("%d.%m.%Y"))
    app.after(1000, update_clock)


def get_weather_coordinates():
    if WEATHER_CONFIG.get("use_coordinates_directly", False):
        return WEATHER_CONFIG["latitude"], WEATHER_CONFIG["longitude"]

    location_name = WEATHER_CONFIG["location_name"]
    geo_url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={location_name}&count=1&language=de&format=json"
    )

    geo_response = requests.get(geo_url, timeout=10)
    geo_response.raise_for_status()
    geo_data = geo_response.json()

    results = geo_data.get("results", [])
    if not results:
        return None, None

    return results[0]["latitude"], results[0]["longitude"]


def update_weather():
    try:
        lat, lon = get_weather_coordinates()

        if lat is None or lon is None:
            weather_temp.configure(text="--°C")
            weather_desc.configure(text="Ort nicht gefunden")
            weather_location.configure(text=WEATHER_CONFIG["location_name"])
            app.after(WEATHER_INTERVAL * 1000, update_weather)
            return

        weather_url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,weather_code"
            f"&timezone={WEATHER_CONFIG['timezone'].replace('/', '%2F')}"
        )

        weather_response = requests.get(weather_url, timeout=10)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        current = weather_data.get("current", {})

        temp = current.get("temperature_2m", "?")
        code = current.get("weather_code", -1)

        weather_map = {
            0: "Klar",
            1: "Überwiegend klar",
            2: "Teilweise bewölkt",
            3: "Bedeckt",
            45: "Neblig",
            48: "Reifnebel",
            51: "Leichter Nieselregen",
            53: "Nieselregen",
            55: "Starker Nieselregen",
            61: "Leichter Regen",
            63: "Regen",
            65: "Starker Regen",
            71: "Leichter Schneefall",
            73: "Schneefall",
            75: "Starker Schneefall",
            80: "Leichte Schauer",
            81: "Schauer",
            82: "Starke Schauer",
            95: "Gewitter",
            96: "Gewitter mit Hagel",
            99: "Starkes Gewitter"
        }

        icon_map = {
            0: "☀",
            1: "🌤",
            2: "⛅",
            3: "☁",
            45: "🌫",
            48: "🌫",
            51: "🌦",
            53: "🌦",
            55: "🌧",
            61: "🌧",
            63: "🌧",
            65: "🌧",
            71: "❄",
            73: "❄",
            75: "❄",
            80: "🌦",
            81: "🌧",
            82: "🌧",
            95: "⛈",
            96: "⛈",
            99: "⛈"
        }

        weather_text = weather_map.get(code, "Unbekannt")
        weather_icon_text = icon_map.get(code, "❔")

        weather_temp.configure(text=f"{temp}°C")
        weather_desc.configure(text=weather_text)
        weather_icon.configure(text=weather_icon_text)
        weather_location.configure(text=WEATHER_CONFIG["location_name"])

    except Exception as e:
        weather_temp.configure(text="--°C")
        weather_desc.configure(text="nicht verfügbar")
        weather_location.configure(text=WEATHER_CONFIG["location_name"])
        print("Wetter Fehler:", e)

    app.after(WEATHER_INTERVAL * 1000, update_weather)


def update_map():
    try:
        map_url = MAP_CONFIG["image_url"]
        response = requests.get(map_url, timeout=15)
        response.raise_for_status()

        image = Image.open(BytesIO(response.content))
        image.thumbnail((MAP_CONFIG["max_width"], MAP_CONFIG["max_height"]))
        map_img = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)

        map_placeholder.configure(image=map_img, text="")
        map_placeholder.image = map_img

    except Exception as e:
        map_placeholder.configure(text="Karte nicht verfügbar")
        print("Karten Fehler:", e)

    app.after(MAP_INTERVAL * 1000, update_map)


def check_alarm():
    global last_alarm

    while True:
        if MONITORING_ENABLED:
            try:
                response = requests.get(URL, timeout=5)
                response.raise_for_status()
                data = response.json()

                current_alarm = data.get("alarm", False)
                current_text = data.get("text", "")

                app.after(0, lambda: server_label.configure(text="Server: erreichbar"))

                if current_alarm:
                    app.after(
                        0,
                        lambda: alarm_label.configure(
                            text=f"ALARM AKTIV: {current_text}",
                            text_color="red"
                        )
                    )
                else:
                    app.after(
                        0,
                        lambda: alarm_label.configure(
                            text="Kein Alarm",
                            text_color="green"
                        )
                    )

                if current_alarm and not last_alarm:
                    if SOUND_ENABLED:
                        play_alarm()
                    show_notification()

                last_alarm = current_alarm

            except Exception as e:
                app.after(0, lambda: server_label.configure(text="Server: nicht erreichbar"))
                app.after(
                    0,
                    lambda: alarm_label.configure(
                        text="Status unbekannt",
                        text_color="orange"
                    )
                )
                print("Fehler:", e)
        else:
            app.after(0, lambda: server_label.configure(text="Überwachung: AUS"))

        time.sleep(CHECK_INTERVAL)


ctk.set_appearance_mode(UI_CONFIG["appearance_mode"])
ctk.set_default_color_theme(UI_CONFIG["color_theme"])

app = ctk.CTk()
app.title(APP_TITLE)
app.state("zoomed")

# MAIN FRAME
main_frame = ctk.CTkFrame(app)
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

# GRID
main_frame.grid_rowconfigure(0, weight=4)
main_frame.grid_rowconfigure(1, weight=2)
main_frame.grid_columnconfigure(0, weight=3)
main_frame.grid_columnconfigure(1, weight=2)

# -------- OBEN LINKS: KARTE --------
map_frame = ctk.CTkFrame(main_frame)
map_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

map_placeholder = ctk.CTkLabel(
    map_frame,
    text="Karte lädt..."
)
map_placeholder.pack(expand=True, fill="both", padx=10, pady=10)

# -------- OBEN RECHTS: UHR + WAPPEN --------
top_right = ctk.CTkFrame(main_frame)
top_right.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)

top_right.grid_rowconfigure(0, weight=1)
top_right.grid_rowconfigure(1, weight=1)
top_right.grid_columnconfigure(0, weight=2)
top_right.grid_columnconfigure(1, weight=1)

clock_font = UI_CONFIG["clock_font_family"]

clock_frame = ctk.CTkFrame(top_right)
clock_frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

time_label = ctk.CTkLabel(clock_frame, text="00:00:00", font=(clock_font, 44, "bold"))
time_label.pack(pady=18)

date_label = ctk.CTkLabel(clock_frame, text="00.00.0000", font=(clock_font, 20))
date_label.pack()

crest_frame = ctk.CTkFrame(top_right)
crest_frame.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)

try:
    crest_path = get_resource_path(UI_CONFIG["crest_file"])
    crest_img_raw = Image.open(crest_path)
    crest_img_raw.thumbnail((200, 200))

    crest_img = ctk.CTkImage(
        light_image=crest_img_raw,
        dark_image=crest_img_raw,
        size=crest_img_raw.size
    )

    crest_label = ctk.CTkLabel(crest_frame, image=crest_img, text="")
    crest_label.image = crest_img
    crest_label.pack(expand=True)

except Exception as e:
    crest_label = ctk.CTkLabel(
        crest_frame,
        text="Wappen\nnicht gefunden",
        font=(clock_font, 18)
    )
    crest_label.pack(expand=True)
    print("Wappen Fehler:", e)

weather_frame = ctk.CTkFrame(top_right)
weather_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)

weather_icon = ctk.CTkLabel(weather_frame, text="☀", font=(clock_font, 48))
weather_icon.pack(pady=5)

weather_temp = ctk.CTkLabel(weather_frame, text="--°C", font=(clock_font, 36, "bold"))
weather_temp.pack()

weather_desc = ctk.CTkLabel(weather_frame, text="lädt...", font=(clock_font, 18))
weather_desc.pack()

weather_location = ctk.CTkLabel(weather_frame, text=WEATHER_CONFIG["location_name"], font=(clock_font, 14))
weather_location.pack(pady=5)

# -------- UNTEN: ALARMBEREICH --------
bottom_frame = ctk.CTkFrame(main_frame)
bottom_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)

bottom_frame.grid_rowconfigure(0, weight=1)
bottom_frame.grid_rowconfigure(1, weight=0)
bottom_frame.grid_columnconfigure(0, weight=3)
bottom_frame.grid_columnconfigure(1, weight=1)
bottom_frame.grid_columnconfigure(2, weight=1)
bottom_frame.grid_columnconfigure(3, weight=1)

alarm_label = ctk.CTkLabel(
    bottom_frame,
    text="KEIN ALARM",
    font=(clock_font, 42, "bold")
)
alarm_label.grid(row=0, column=0, columnspan=4, pady=35)

server_label = ctk.CTkLabel(
    bottom_frame,
    text="Server: unbekannt",
    font=(clock_font, 16)
)
server_label.grid(row=1, column=0, sticky="sw", padx=15, pady=10)

sound_button = ctk.CTkButton(
    bottom_frame,
    text=f"Ton: {'AN' if SOUND_ENABLED else 'AUS'}",
    width=120,
    command=toggle_sound
)
sound_button.grid(row=1, column=1, sticky="se", padx=8, pady=10)

monitoring_button = ctk.CTkButton(
    bottom_frame,
    text=f"Überwachung: {'AN' if MONITORING_ENABLED else 'AUS'}",
    width=150,
    command=toggle_monitoring
)
monitoring_button.grid(row=1, column=2, sticky="se", padx=15, pady=10)

update_button = ctk.CTkButton(
    bottom_frame,
    text="Update prüfen",
    width=130,
    command=check_for_update,
    state="normal"
)
update_button.grid(row=1, column=3, sticky="se", padx=15, pady=10)

update_clock()
update_weather()
update_map()

thread = threading.Thread(target=check_alarm, daemon=True)
thread.start()

app.after(3000, check_for_update)

app.mainloop()
