from dataclasses import dataclass,field
from enum import Enum, auto
import asyncio
import serial

from generic_utils.io.loggerConfig import getSerialLogger 

logger = getSerialLogger()


# ---------------------------------------------------------
# State Machine
# ---------------------------------------------------------

class RxState(Enum):
    IDLE = auto()
    CYCLIC = auto()
    COLLECT = auto()


@dataclass
class ParserState:
    state: RxState = RxState.IDLE
    buffer: bytearray = field(default_factory=bytearray)


# ---------------------------------------------------------
# Struktur-Erkennungsfunktionen
# ---------------------------------------------------------
   
def is_ZT(msg: bytes) -> bool:
    """Erkennt Zeitformat: dd.dd.dd;dd:dd:dd"""
    try:
        s = msg.decode()

        if len(s) != 17:
            return False

        if s.count(".") != 2:
            return False

        if s.count(":") != 2:
            return False

        if s.count(";") != 1:
            return False

        # Struktur prüfen
        return (
            s[2] == "." and
            s[5] == "." and
            s[8] == ";" and
            s[11] == ":" and
            s[14] == ":"
        )
    except:
        return False

def is_DA(msg: bytes) -> bool:
    """DA: mehrere Felder, alle außer letztem haben Punkt"""
    try:
        s = msg.decode()

        if len(s) != 20:
            return False

        if ":" in s:     # DA hat NIE Doppelpunkte
            return False
        
        if s.count(";") != 3:
            return False

        if s.count(".") != 3:
            return False

        parts = s.split(";")
        if len(parts) < 2:
            return False

        # alle außer letztem müssen Punkt haben
        if not all("." in p for p in parts[:-1]):
            return False

        # letztes Feld darf keinen Punkt haben
        if "." in parts[-1]:
            return False

        return True
    except:
        return False




def is_valid_number(field: str) -> bool:
    """Erlaubt: ±Zahl, optional mit Punkt"""
    if not field:
        return False

    # Vorzeichen entfernen
    if field[0] in "+-":
        field = field[1:]

    # Punkt optional
    if "." in field:
        left, right = field.split(".", 1)
        return left.isdigit() and right.isdigit()

    return field.isdigit()


def is_DD(msg: bytes) -> bool:
    """DD: mehrere Felder, jedes Feld ist gültige Zahl (mit/ohne Punkt, mit/ohne Vorzeichen)"""
    try:
        s = msg.decode()

        if len(s) != 58:
            return False

        if ":" in s:     # DD hat NIE Doppelpunkte
            return False
        
        if s.count(";") != 12:
            return False
        
        parts = s.split(";")
        if len(parts) < 2:
            return False

        return all(is_valid_number(p) for p in parts)
    except:
        return False


def is_DX(msg: bytes) -> bool:
    """DX: mehrere Felder, jedes Feld ist '0' oder '1'"""
    try:
        s = msg.decode()

        if len(s) != 31:
            return False

        if "." in s or ":" in s:
            return False
        
        if s.count(";") != 15:
            return False
        
        parts = s.split(";")
        if len(parts) < 2:
            return False

        return all(p in ("0", "1") for p in parts)
    except:
        return False


# ---------------------------------------------------------
# Parser-Funktion
# ---------------------------------------------------------

async def read_bytes_cases(
    ser: serial.Serial,
    num: int,
    marker: bytes | None,   # z.B. b"!AB12"
    timeout: float = 1.0,
    stx: int = 0x02,
    etx: int = 0x03,
) -> bytearray | None:

    ps = ParserState()
    result = bytearray()

    ASCII_ALLOWED = b"0123456789+-.:;"

    end_time = asyncio.get_event_loop().time() + timeout

    while True:

        # Timeout
        if asyncio.get_event_loop().time() > end_time:
            return None

        if ser.in_waiting == 0:
            await asyncio.sleep(0.001)
            continue

        b = ser.read(1)
        if not b:
            continue

        byte = b[0]

        match ps.state:

            # ---------------------------------------------------
            # IDLE → Warten auf Start
            # ---------------------------------------------------
            case RxState.IDLE:

                # Zyklisches Paket beginnt
                if byte == stx:
                    ps.state = RxState.CYCLIC
                    ps.buffer.clear()
                    continue

                # Marker‑Antwort beginnt
                if marker and byte == marker[0]:
                    result = bytearray(b)
                    ps.state = RxState.COLLECT
                    continue

                # ASCII‑Antwort beginnt
                if byte in ASCII_ALLOWED:
                    result = bytearray(b)
                    ps.state = RxState.COLLECT
                    continue

                # Müll → ignorieren
                continue

            # ---------------------------------------------------
            # CYCLIC → Zyklisches Paket verwerfen
            # ---------------------------------------------------
            case RxState.CYCLIC:

                if byte == etx:
                    ps.state = RxState.IDLE
                    ps.buffer.clear()
                    logger.debug(f"Discard cyclic data")
                    continue

                ps.buffer.append(byte)

                # Schutz gegen endlose Pakete
                if len(ps.buffer) > 4096:
                    ps.state = RxState.IDLE
                    ps.buffer.clear()

                continue

            # ---------------------------------------------------
            # COLLECT → Antwort sammeln
            # ---------------------------------------------------
            case RxState.COLLECT:

                result.extend(b)

                # Marker‑Antwort → Länge erreicht?
                if marker and result.startswith(marker):
                    if len(result) >= num:
                        logger.debug(f"Marker:RX {len(result)} bytes: {result.hex(' ')}")
                        return result

                # ASCII‑Antwort → Struktur prüfen
                if all(c in ASCII_ALLOWED for c in result):

                    if is_ZT(result):
                        logger.debug(f"ZT: RX {len(result)} bytes: {result.hex(' ')}")
                        return result

                    if is_DA(result):
                        logger.debug(f"DA: RX {len(result)} bytes: {result.hex(' ')}")
                        return result

                    if is_DD(result):
                        logger.debug(f"DD: RX {len(result)} bytes: {result.hex(' ')}")
                        return result

                    if is_DX(result):
                        logger.debug(f"DX: RX {len(result)} bytes: {result.hex(' ')}")
                        return result

                # Wenn zu lang → ungültig
                if len(result) > 256:
                    ps.state = RxState.IDLE
                    result.clear()
                    logger.error(f"Collecting data was not successfull")
                    continue

                continue
