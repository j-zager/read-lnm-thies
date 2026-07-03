import serial
from serial import Serial
from typing import Dict, Tuple, List
from tqdm import tqdm


# -----------------------------
# Konfiguration
# -----------------------------

BAUDRATES: List[int] = [
    1200, 2400, 4800, 9600,
    19200, 38400, 57600, 115200
]

PARITIES: Dict[str, str] = {
    "N": serial.PARITY_NONE,
    "E": serial.PARITY_EVEN,
    "O": serial.PARITY_ODD
}

#PORT: str = "/dev/ttyUSB0"   # anpassen
PORT: str = "/dev/ttyACM0"   # anpassen
COMMAND: str = "ID"
TIMEOUT: float = 0.15


# -----------------------------
# Hilfsfunktionen
# -----------------------------

def build_request(addr: int) -> bytes:
    """Erzeugt xxBB<CR>."""
    return f"{addr:02d}{COMMAND}\r".encode("ascii")


def parse_response(resp: bytes) -> str | None:
    """Validiert Antwortformat !xxBBppppp."""
    decoded = resp.decode(errors="ignore")
    print(f"DEBUG RAW → '{decoded}'")

    if len(decoded) != 10:
        return None
    if not decoded.startswith("!"):
        return None

    return decoded


def open_port(baud: int, parity: str) -> Serial | None:
    """Öffnet Port mit Parametern."""
    try:
        return Serial(
            port=PORT,
            baudrate=baud,
            parity=parity,
            bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_ONE,
            timeout=TIMEOUT,
            write_timeout=0.1
        )
    except Exception:
        print(f"Error at parity:{parity} and baudrate:{baud}")
        return None


# -----------------------------
# Hauptscan
# -----------------------------

def scan() -> Tuple[int, str, int, str] | None:
    """Testet alle Kombinationen und gibt Treffer zurück."""
    total = len(BAUDRATES) * len(PARITIES) * 100

    with tqdm(total=total, desc="RS485 Scan", unit="test") as bar:
        for baud in BAUDRATES:
            for parity_name, parity_value in PARITIES.items():

                ser = open_port(baud, parity_value)
                if ser is None:
                    bar.update(100)
                    continue

                for addr in range(100):
                    bar.update(1)

                    req = build_request(addr)

                    ser.reset_input_buffer()
                    ser.reset_output_buffer()

                    try:
                        ser.write(req)
                    except Exception:
                        continue

                    resp = ser.read(10)
                    if not resp:
                        continue

                    parsed = parse_response(resp)
                    if parsed is None:
                        continue

                    if parsed[1:3] == f"{addr:02d}" and parsed[3:5] == COMMAND:
                        ser.close()
                        return baud, parity_name, addr, parsed

                ser.close()

    return None


# -----------------------------
# Start
# -----------------------------

if __name__ == "__main__":
    result = scan()

    if result is None:
        print("\n!!! KEINE KOMBINATION GEFUNDEN !!!")
        print("→ Prüfe A/B‑Vertauschung, Terminierung, Versorgung, Buslast.")
    else:
        baud, parity, addr, answer = result
        print("\n=== KOMBINATION GEFUNDEN ===")
        print(f"Baudrate : {baud}")
        print(f"Parität  : {parity}")
        print(f"Adresse  : {addr:02d}")
        print(f"Antwort  : {answer}")


