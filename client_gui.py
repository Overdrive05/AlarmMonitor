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

APP_VERSION = "1.0.8"

VERSION_URL = "https://github.com/Overdrive05/AlarmMonitor/releases/latest/download/version.txt"
UPDATER_URL = "https://github.com/Overdrive05/AlarmMonitor/releases/latest/download/updater.exe"
NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

def get_base_path():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_resource_path(filename):
    return os.path.join(get_base_path(), filename)


def cache_busted_url(url):
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}_={int(time.time())}"


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

COLORS = {
    "bg": UI_CONFIG.get("background_color", "#07111f"),
    "panel": UI_CONFIG.get("panel_color", "#101b2b"),
    "panel_alt": UI_CONFIG.get("panel_alt_color", "#142235"),
    "line": "#223047",
    "text": UI_CONFIG.get("primary_text_color", "#f8fafc"),
    "muted": UI_CONFIG.get("muted_text_color", "#94a3b8"),
    "accent": UI_CONFIG.get("accent_color", "#2f81f7"),
    "normal": UI_CONFIG.get("normal_color", "#2fbf71"),
    "alarm": UI_CONFIG.get("alarm_color", "#ff4d4f"),
    "warning": UI_CONFIG.get("warning_color", "#f5a524"),
    "button": "#1f6feb",
    "button_hover": "#388bfd"
}

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
            response = requests.get(
                cache_busted_url(VERSION_URL),
                timeout=10,
                headers=NO_CACHE_HEADERS
            )
            response.raise_for_status()
            online_version = response.text.strip()
            app.after(0, lambda version=online_version: apply_update_state(online_version=version))
        except Exception as e:
            app.after(0, lambda error=e: apply_update_state(error=error))

    threading.Thread(target=worker, daemon=True).start()


def refresh_updater(updater_path):
    temp_path = updater_path + ".new"

    try:
        response = requests.get(
            cache_busted_url(UPDATER_URL),
            timeout=30,
            headers=NO_CACHE_HEADERS
        )
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

        subprocess.Popen([updater_path, "--pid", str(os.getpid())], cwd=get_base_path())
        app.destroy()
    except Exception as e:
        update_button.configure(
            text="Update Fehler",
            state="normal",
            command=check_for_update
        )
        print("Update Fehler:", e)


def style_toggle_button(button, enabled, on_text, off_text):
    button.configure(
        text=on_text if enabled else off_text,
        fg_color=COLORS["normal"] if enabled else COLORS["panel_alt"],
        hover_color=COLORS["normal"] if enabled else COLORS["line"],
        text_color="#06131f" if enabled else COLORS["text"]
    )


def toggle_sound():
    global SOUND_ENABLED
    SOUND_ENABLED = not SOUND_ENABLED
    style_toggle_button(sound_button, SOUND_ENABLED, "Ton AN", "Ton AUS")


def toggle_monitoring():
    global MONITORING_ENABLED
    MONITORING_ENABLED = not MONITORING_ENABLED
    style_toggle_button(
        monitoring_button,
        MONITORING_ENABLED,
        "Überwachung AN",
        "Überwachung AUS"
    )


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


def set_server_state(text, state):
    state_colors = {
        "ok": COLORS["normal"],
        "error": COLORS["alarm"],
        "off": COLORS["warning"],
        "unknown": COLORS["muted"]
    }
    color = state_colors.get(state, COLORS["muted"])
    server_label.configure(text=text, text_color=color)
    server_chip.configure(text=text.replace("Server: ", ""), fg_color=color, text_color="#06131f")


def set_alarm_state(active, text=""):
    if active:
        message = text.strip() or "Einsatz"
        alarm_label.configure(
            text=f"ALARM AKTIV: {message}",
            text_color=COLORS["alarm"]
        )
        alarm_hint_label.configure(text="Alarmmeldung vom Server", text_color=COLORS["alarm"])
        alarm_frame.configure(fg_color="#2a1216", border_color=COLORS["alarm"])
        alarm_badge.configure(text="ALARM", fg_color=COLORS["alarm"], text_color="#21060a")
    else:
        alarm_label.configure(text="Kein Alarm", text_color=COLORS["normal"])
        alarm_hint_label.configure(text="System bereit", text_color=COLORS["muted"])
        alarm_frame.configure(fg_color=COLORS["panel"], border_color=COLORS["normal"])
        alarm_badge.configure(text="BEREIT", fg_color=COLORS["normal"], text_color="#06131f")


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

                app.after(0, lambda: set_server_state("Server: erreichbar", "ok"))

                if current_alarm:
                    app.after(0, lambda text=current_text: set_alarm_state(True, text))
                else:
                    app.after(0, lambda: set_alarm_state(False))

                if current_alarm and not last_alarm:
                    if SOUND_ENABLED:
                        play_alarm()
                    show_notification()

                last_alarm = current_alarm

            except Exception as e:
                app.after(0, lambda: set_server_state("Server: nicht erreichbar", "error"))
                app.after(0, lambda: set_alarm_state(False))
                app.after(0, lambda: alarm_hint_label.configure(text="Status unbekannt", text_color=COLORS["warning"]))
                print("Fehler:", e)
        else:
            app.after(0, lambda: set_server_state("Überwachung: AUS", "off"))

        time.sleep(CHECK_INTERVAL)


ctk.set_appearance_mode(UI_CONFIG["appearance_mode"])
ctk.set_default_color_theme(UI_CONFIG["color_theme"])

app = ctk.CTk()
app.title(APP_TITLE)
app.configure(fg_color=COLORS["bg"])
app.minsize(1180, 720)
try:
    app.state("zoomed")
except Exception:
    app.geometry("1280x780")

clock_font = UI_CONFIG["clock_font_family"]
station_name = UI_CONFIG.get("station_name", "Feuerwehr Raunheim")
map_title = UI_CONFIG.get("map_title", "Warnkarte")

root_frame = ctk.CTkFrame(app, fg_color=COLORS["bg"], corner_radius=0)
root_frame.pack(fill="both", expand=True, padx=18, pady=18)
root_frame.grid_columnconfigure(0, weight=1)
root_frame.grid_rowconfigure(1, weight=1)

header_frame = ctk.CTkFrame(
    root_frame,
    fg_color=COLORS["panel"],
    corner_radius=8,
    border_width=1,
    border_color=COLORS["line"]
)
header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 14))
header_frame.grid_columnconfigure(0, weight=1)
header_frame.grid_columnconfigure(1, weight=0)

title_stack = ctk.CTkFrame(header_frame, fg_color="transparent")
title_stack.grid(row=0, column=0, sticky="w", padx=18, pady=14)

title_label = ctk.CTkLabel(
    title_stack,
    text=APP_TITLE.upper(),
    font=(clock_font, 24, "bold"),
    text_color=COLORS["text"]
)
title_label.pack(anchor="w")

station_label = ctk.CTkLabel(
    title_stack,
    text=station_name,
    font=(clock_font, 13),
    text_color=COLORS["muted"]
)
station_label.pack(anchor="w", pady=(2, 0))

header_status = ctk.CTkFrame(header_frame, fg_color="transparent")
header_status.grid(row=0, column=1, sticky="e", padx=18, pady=14)

version_chip = ctk.CTkLabel(
    header_status,
    text=f"Version {APP_VERSION}",
    width=116,
    height=30,
    fg_color=COLORS["panel_alt"],
    corner_radius=8,
    font=(clock_font, 12, "bold"),
    text_color=COLORS["muted"]
)
version_chip.pack(side="left", padx=(0, 8))

server_chip = ctk.CTkLabel(
    header_status,
    text="unbekannt",
    width=150,
    height=30,
    fg_color=COLORS["muted"],
    corner_radius=8,
    font=(clock_font, 12, "bold"),
    text_color="#06131f"
)
server_chip.pack(side="left")

main_frame = ctk.CTkFrame(root_frame, fg_color="transparent")
main_frame.grid(row=1, column=0, sticky="nsew")
main_frame.grid_columnconfigure(0, weight=7)
main_frame.grid_columnconfigure(1, weight=3)
main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_rowconfigure(1, weight=0)

map_frame = ctk.CTkFrame(
    main_frame,
    fg_color=COLORS["panel"],
    corner_radius=8,
    border_width=1,
    border_color=COLORS["line"]
)
map_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 14), pady=(0, 14))
map_frame.grid_columnconfigure(0, weight=1)
map_frame.grid_rowconfigure(1, weight=1)

map_header = ctk.CTkFrame(map_frame, fg_color="transparent")
map_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))
map_header.grid_columnconfigure(0, weight=1)

map_title_label = ctk.CTkLabel(
    map_header,
    text=map_title,
    font=(clock_font, 16, "bold"),
    text_color=COLORS["text"]
)
map_title_label.grid(row=0, column=0, sticky="w")

map_subtitle_label = ctk.CTkLabel(
    map_header,
    text="Automatisch aktualisiert",
    font=(clock_font, 12),
    text_color=COLORS["muted"]
)
map_subtitle_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

map_canvas = ctk.CTkFrame(map_frame, fg_color=COLORS["panel_alt"], corner_radius=8)
map_canvas.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))

map_placeholder = ctk.CTkLabel(
    map_canvas,
    text="Karte lädt...",
    font=(clock_font, 18, "bold"),
    text_color=COLORS["muted"]
)
map_placeholder.pack(expand=True, fill="both", padx=12, pady=12)

side_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
side_frame.grid(row=0, column=1, sticky="nsew", pady=(0, 14))
side_frame.grid_columnconfigure(0, weight=1)
side_frame.grid_rowconfigure(0, weight=0)
side_frame.grid_rowconfigure(1, weight=1)
side_frame.grid_rowconfigure(2, weight=1)

clock_frame = ctk.CTkFrame(
    side_frame,
    fg_color=COLORS["panel"],
    corner_radius=8,
    border_width=1,
    border_color=COLORS["line"]
)
clock_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))

time_label = ctk.CTkLabel(
    clock_frame,
    text="00:00:00",
    font=(clock_font, 50, "bold"),
    text_color=COLORS["text"]
)
time_label.pack(anchor="w", padx=18, pady=(16, 0))

date_label = ctk.CTkLabel(
    clock_frame,
    text="00.00.0000",
    font=(clock_font, 18),
    text_color=COLORS["muted"]
)
date_label.pack(anchor="w", padx=20, pady=(0, 16))

weather_frame = ctk.CTkFrame(
    side_frame,
    fg_color=COLORS["panel"],
    corner_radius=8,
    border_width=1,
    border_color=COLORS["line"]
)
weather_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 12))
weather_frame.grid_columnconfigure(0, weight=0)
weather_frame.grid_columnconfigure(1, weight=1)
weather_frame.grid_rowconfigure(0, weight=1)

weather_icon = ctk.CTkLabel(
    weather_frame,
    text="☀",
    width=86,
    font=(clock_font, 52),
    text_color=COLORS["warning"]
)
weather_icon.grid(row=0, column=0, sticky="ns", padx=(18, 8), pady=18)

weather_stack = ctk.CTkFrame(weather_frame, fg_color="transparent")
weather_stack.grid(row=0, column=1, sticky="nsew", padx=(0, 18), pady=18)

weather_location = ctk.CTkLabel(
    weather_stack,
    text=WEATHER_CONFIG["location_name"],
    font=(clock_font, 14, "bold"),
    text_color=COLORS["muted"]
)
weather_location.pack(anchor="w")

weather_temp = ctk.CTkLabel(
    weather_stack,
    text="--°C",
    font=(clock_font, 42, "bold"),
    text_color=COLORS["text"]
)
weather_temp.pack(anchor="w", pady=(2, 0))

weather_desc = ctk.CTkLabel(
    weather_stack,
    text="lädt...",
    font=(clock_font, 15),
    text_color=COLORS["muted"]
)
weather_desc.pack(anchor="w")

crest_frame = ctk.CTkFrame(
    side_frame,
    fg_color=COLORS["panel"],
    corner_radius=8,
    border_width=1,
    border_color=COLORS["line"]
)
crest_frame.grid(row=2, column=0, sticky="nsew")
crest_frame.grid_columnconfigure(0, weight=1)
crest_frame.grid_rowconfigure(1, weight=1)

crest_title = ctk.CTkLabel(
    crest_frame,
    text="Einheit",
    font=(clock_font, 14, "bold"),
    text_color=COLORS["muted"]
)
crest_title.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))

try:
    crest_path = get_resource_path(UI_CONFIG["crest_file"])
    crest_img_raw = Image.open(crest_path)
    crest_img_raw.thumbnail((190, 190))

    crest_img = ctk.CTkImage(
        light_image=crest_img_raw,
        dark_image=crest_img_raw,
        size=crest_img_raw.size
    )

    crest_label = ctk.CTkLabel(crest_frame, image=crest_img, text="")
    crest_label.image = crest_img
    crest_label.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

except Exception as e:
    crest_label = ctk.CTkLabel(
        crest_frame,
        text="Wappen\nnicht gefunden",
        font=(clock_font, 18, "bold"),
        text_color=COLORS["warning"]
    )
    crest_label.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
    print("Wappen Fehler:", e)

alarm_frame = ctk.CTkFrame(
    main_frame,
    fg_color=COLORS["panel"],
    corner_radius=8,
    border_width=1,
    border_color=COLORS["normal"]
)
alarm_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
alarm_frame.grid_columnconfigure(0, weight=1)
alarm_frame.grid_columnconfigure(1, weight=0)

alarm_text_stack = ctk.CTkFrame(alarm_frame, fg_color="transparent")
alarm_text_stack.grid(row=0, column=0, sticky="ew", padx=18, pady=18)

alarm_badge = ctk.CTkLabel(
    alarm_text_stack,
    text="BEREIT",
    width=92,
    height=28,
    fg_color=COLORS["normal"],
    corner_radius=8,
    font=(clock_font, 12, "bold"),
    text_color="#06131f"
)
alarm_badge.pack(anchor="w")

alarm_label = ctk.CTkLabel(
    alarm_text_stack,
    text="Kein Alarm",
    font=(clock_font, 42, "bold"),
    text_color=COLORS["normal"]
)
alarm_label.pack(anchor="w", pady=(6, 0))

alarm_hint_label = ctk.CTkLabel(
    alarm_text_stack,
    text="System bereit",
    font=(clock_font, 14),
    text_color=COLORS["muted"]
)
alarm_hint_label.pack(anchor="w")

control_frame = ctk.CTkFrame(alarm_frame, fg_color="transparent")
control_frame.grid(row=0, column=1, sticky="e", padx=18, pady=18)

server_label = ctk.CTkLabel(
    control_frame,
    text="Server: unbekannt",
    font=(clock_font, 14, "bold"),
    text_color=COLORS["muted"]
)
server_label.grid(row=0, column=0, columnspan=3, sticky="e", pady=(0, 10))

sound_button = ctk.CTkButton(
    control_frame,
    text="Ton AN",
    width=118,
    height=38,
    corner_radius=8,
    command=toggle_sound
)
sound_button.grid(row=1, column=0, sticky="e", padx=(0, 8))

monitoring_button = ctk.CTkButton(
    control_frame,
    text="Überwachung AN",
    width=156,
    height=38,
    corner_radius=8,
    command=toggle_monitoring
)
monitoring_button.grid(row=1, column=1, sticky="e", padx=(0, 8))

update_button = ctk.CTkButton(
    control_frame,
    text="Update prüfen",
    width=130,
    height=38,
    corner_radius=8,
    fg_color=COLORS["button"],
    hover_color=COLORS["button_hover"],
    command=check_for_update,
    state="normal"
)
update_button.grid(row=1, column=2, sticky="e")

style_toggle_button(sound_button, SOUND_ENABLED, "Ton AN", "Ton AUS")
style_toggle_button(monitoring_button, MONITORING_ENABLED, "Überwachung AN", "Überwachung AUS")
set_alarm_state(False)
set_server_state("Server: unbekannt", "unknown")

update_clock()
app.after(100, update_weather)
app.after(250, update_map)

thread = threading.Thread(target=check_alarm, daemon=True)
thread.start()

app.after(3000, check_for_update)

app.mainloop()
