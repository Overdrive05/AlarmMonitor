import os
import sys
import time
import requests
import subprocess

EXE_NAME = "client_gui.exe"
VERSION_FILE = "version.txt"
MIN_EXE_SIZE = 1_000_000

VERSION_URL = "https://github.com/Overdrive05/AlarmMonitor/releases/latest/download/version.txt"
EXE_URL = "https://github.com/Overdrive05/AlarmMonitor/releases/latest/download/client_gui.exe"


def get_base_path():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def download_file(url, destination, timeout):
    with requests.get(url, timeout=timeout, stream=True) as response:
        response.raise_for_status()

        with open(destination, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)


def validate_exe(path):
    if os.path.getsize(path) < MIN_EXE_SIZE:
        raise RuntimeError("Heruntergeladene EXE ist unerwartet klein.")

    with open(path, "rb") as f:
        if f.read(2) != b"MZ":
            raise RuntimeError("Heruntergeladene Datei ist keine Windows-EXE.")


def fetch_version():
    response = requests.get(VERSION_URL, timeout=10)
    response.raise_for_status()
    version = response.text.strip()

    if not version:
        raise RuntimeError("Versionsdatei ist leer.")

    return version


def replace_with_retry(source, target, attempts=15, delay=1):
    last_error = None

    for _ in range(attempts):
        try:
            os.replace(source, target)
            return
        except PermissionError as e:
            last_error = e
            time.sleep(delay)

    if last_error:
        raise last_error


def main():
    base_path = get_base_path()

    exe_path = os.path.join(base_path, EXE_NAME)
    new_exe_path = os.path.join(base_path, "client_gui_new.exe")
    version_path = os.path.join(base_path, VERSION_FILE)
    new_version_path = os.path.join(base_path, "version_new.txt")

    for temp_path in (new_exe_path, new_version_path):
        if os.path.exists(temp_path):
            os.remove(temp_path)

    time.sleep(2)

    print("Lade neue Version...")

    download_file(EXE_URL, new_exe_path, timeout=60)
    validate_exe(new_exe_path)
    online_version = fetch_version()

    with open(new_version_path, "w", encoding="utf-8") as f:
        f.write(online_version + "\n")

    print("Ersetze alte EXE...")
    replace_with_retry(new_exe_path, exe_path)

    print("Aktualisiere Version...")
    os.replace(new_version_path, version_path)

    print("Starte App neu...")
    subprocess.Popen([exe_path], cwd=base_path)

    print("Update fertig.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        base_path = get_base_path()
        for temp_name in ("client_gui_new.exe", "version_new.txt"):
            temp_path = os.path.join(base_path, temp_name)
            if os.path.exists(temp_path):
                os.remove(temp_path)

        print("Update Fehler:", e)
        input("Drücke Enter zum Schließen...")
