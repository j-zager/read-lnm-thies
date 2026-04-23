# Linux virtual ports /dev/pts/<nummer>
# socat -d -d pty,raw,echo=0,mode=666 pty,raw,echo=0,mode=666

import serial
import serial.tools.list_ports
from generic_utils.io.loggerConfig import getSerialLogger 
import os

logger = getSerialLogger()


def init_virtual_port_selection() -> str | None:
    # Frage, ob virtueller Port genutzt werden soll
    while True:
        use_virtual = input("Virtuellen Port verwenden? (j/n): ").strip().lower()

        if use_virtual in ("j", "n"):
            break
        print("Bitte 'j' oder 'n' eingeben.")

    if use_virtual == "n":
        return None

    # Wenn ja → PTY-ID abfragen
    while True:
        port_id = input("Bitte PTY-ID eingeben (z.B. 4 oder 5): ").strip()

        if not port_id.isdigit():
            print("Ungültige Eingabe – bitte eine Zahl eingeben.")
            continue

        port_id = int(port_id)
        port_path = f"/dev/pts/{port_id}"

        # Existiert der Port?
        if not os.path.exists(port_path):
            print(f"Port {port_path} existiert nicht. Bitte erneut versuchen.")
            continue

        # Alles OK → zurückgeben
        return port_path


def is_pty(port: str) -> bool:
    return port.startswith("/dev/pts/")


def scan_pts_devices() -> list[str]:
    pts_dir = "/dev/pts"
    pts = []

    for entry in os.listdir(pts_dir):
        # PTY devices are numeric (0,1,2,...)
        if entry.isdigit():
            pts.append(f"/dev/pts/{entry}")

    return pts


def find_virtual_ports() -> list[str]:
    return [p.device for p in serial.tools.list_ports.comports()
            if "/dev/pts/" in p.device]


def auto_select_virtual_port(portId:int=0) -> str | None:
    # 1. Try comports() first
    vports = find_virtual_ports()

    # 2. If empty → fallback to scanning /dev/pts
    if not vports:
        vports = scan_pts_devices()

    # 3. Filter out PTYs that are not writable
    vports = [p for p in vports if os.access(p, os.W_OK)]

    if not vports:
        return None

    if portId < len(vports):
        logger.info(f"Auto-selected virtual port: {vports[portId]}")
        return vports[portId]

    return None



def smart_select_port(portId:int=0) -> str | None:
    # 1. Check for virtual ports (socat)
    vport = auto_select_virtual_port(portId=portId)
    if vport:
        return vport

    # 2. No virtual ports → ask user
    return None




