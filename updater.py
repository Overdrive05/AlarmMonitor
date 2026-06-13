import argparse
import ctypes
import os
import subprocess
import sys
import time

import requests

EXE_NAME = "client_gui.exe"
VERSION_FILE = "version.txt"
MIN_EXE_SIZE = 1_000_000

DOWNLOAD_EXE_NAME = "client_gui.download.exe"
DOWNLOAD_VERSION_NAME = "version.download.txt"
STALE_TEMP_NAMES = (
    "client_gui_new.exe",
    "version_new.txt",
    DOWNLOAD_EXE_NAME,
    DOWNLOAD_VERSION_NAME,
)

VERSION_URL = "https://github.com/Overdrive05/AlarmMonitor/releases/latest/download/version.txt"
EXE_URL = "https://github.com/Overdrive05/AlarmMonitor/releases/latest/download/client_gui.exe"
NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}


def get_base_path():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def cache_busted_url(url):
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}_={int(time.time())}"


def parse_args():
    parser = argparse.ArgumentParser(description="AlarmMonitor Updater")
    parser.add_argument(
        "--pid",
        type=int,
        default=None,
        help="PID der laufenden client_gui.exe, auf deren Ende gewartet werden soll.",
    )
    return parser.parse_args()


def cleanup_temp_files(base_path):
    for temp_name in STALE_TEMP_NAMES:
        temp_path = os.path.join(base_path, temp_name)
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except PermissionError:
                print(f"{temp_name} ist noch in Benutzung und wird uebersprungen.")


def wait_for_pid(pid, timeout=30):
    if not pid or os.name != "nt":
        return

    synchronize = 0x00100000
    wait_timeout = 0x00000102
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(synchronize, False, pid)

    if not handle:
        return

    try:
        result = kernel32.WaitForSingleObject(handle, int(timeout * 1000))
        if result == wait_timeout:
            print("App laeuft noch, warte beim Ersetzen weiter...")
    finally:
        kernel32.CloseHandle(handle)


def download_file(url, destination, timeout):
    with requests.get(
        cache_busted_url(url),
        timeout=timeout,
        stream=True,
        headers=NO_CACHE_HEADERS
    ) as response:
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
    response = requests.get(
        cache_busted_url(VERSION_URL),
        timeout=10,
        headers=NO_CACHE_HEADERS
    )
    response.raise_for_status()
    version = response.text.strip()

    if not version:
        raise RuntimeError("Versionsdatei ist leer.")

    return version


def replace_with_retry(source, target, attempts=90, delay=0.5):
    last_error = None

    for attempt in range(1, attempts + 1):
        try:
            os.replace(source, target)
            return
        except PermissionError as e:
            last_error = e
        except OSError as e:
            if getattr(e, "winerror", None) not in (5, 32):
                raise
            last_error = e

        if attempt in (1, 20, 50):
            print("client_gui.exe ist noch gesperrt, warte...")

        time.sleep(delay)

    raise RuntimeError(
        "client_gui.exe konnte nicht ersetzt werden. "
        "Bitte AlarmMonitor komplett schliessen und updater.exe erneut starten."
    ) from last_error


def main():
    args = parse_args()
    base_path = get_base_path()

    exe_path = os.path.join(base_path, EXE_NAME)
    download_exe_path = os.path.join(base_path, DOWNLOAD_EXE_NAME)
    version_path = os.path.join(base_path, VERSION_FILE)
    download_version_path = os.path.join(base_path, DOWNLOAD_VERSION_NAME)

    cleanup_temp_files(base_path)
    wait_for_pid(args.pid)

    print("Lade neue Version...")
    download_file(EXE_URL, download_exe_path, timeout=60)
    validate_exe(download_exe_path)
    online_version = fetch_version()

    with open(download_version_path, "w", encoding="utf-8") as f:
        f.write(online_version + "\n")

    print("Ersetze alte EXE...")
    replace_with_retry(download_exe_path, exe_path)

    print("Aktualisiere Version...")
    os.replace(download_version_path, version_path)

    print("Starte App neu...")
    subprocess.Popen([exe_path], cwd=base_path)

    cleanup_temp_files(base_path)
    print("Update fertig.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        base_path = get_base_path()
        cleanup_temp_files(base_path)

        print("Update Fehler:", e)
        input("Druecke Enter zum Schliessen...")
