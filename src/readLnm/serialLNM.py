from dataclasses import dataclass,field
from enum import Enum, auto
import asyncio
import serial

from generic_utils.io.loggerConfig import getSerialLogger
from readLnm.specialLnmCommands import parse_DA,parse_DX,parse_DD,parse_ZT

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

        parts = s.split(";")
        if len(parts) < 2:
            return False
        
        if not (s[5] == ";" and s[11] == ";" and s[16] == ";"):
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
    stx: bytes = b"\x02",
    etx: bytes = b"\x03",
) -> bytearray | None:
    

    ps = ParserState()
    ps.state = RxState.IDLE
    result = bytearray()

    wrg_cmd_marker = None
    # Fehler-Marker erzeugen: "!00CI"
    if marker is not None and len(marker)>=5:
        wrg_cmd_marker = marker[0:3] + b"CI"

    ASCII_ALLOWED = b"0123456789+-.:;"

    end_time = asyncio.get_event_loop().time() + timeout
    logger.info("print all received bytes/n")

    print(f">>>>>>>>>> Start:", end="")
    
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

        print(f"0x{b[0]:02X} ", end="")
        #print(f"0x{b[0]:02X} ")


        match ps.state:

            # ---------------------------------------------------
            # IDLE → Warten auf Start
            # ---------------------------------------------------
            case RxState.IDLE:
                #logger.info("RxState.IDLE")

                # Zyklisches Paket beginnt
                if b == stx:
                    ps.state = RxState.CYCLIC
                    ps.buffer.clear()
                    ps.buffer.append(b[0])
                    logger.info(f"STX: start cyclic data detected ")
                    continue

                # Marker‑Antwort beginnt
                if marker and b[0] == marker[0]:
                    result = bytearray(b)
                    ps.state = RxState.COLLECT
                    logger.info(f"Start of marker response detected ")
                    continue

                # ASCII‑Antwort beginnt
                if b in ASCII_ALLOWED:
                    logger.info(f"ascii response starts")
                    result = bytearray(b)
                    ps.state = RxState.COLLECT
                    continue

                # Müll → ignorieren
                continue

            # ---------------------------------------------------
            # CYCLIC → Zyklisches Paket verwerfen
            # ---------------------------------------------------
            case RxState.CYCLIC:
                #logger.info("RxState.Cyclic")

                if b == etx:
                    ps.state = RxState.IDLE
                    ps.buffer.clear()
                    logger.info(f"ETX:Discard cyclic data")
                    print(" ####### ",end="")
                    continue

                ps.buffer.append(b[0])

                # Schutz gegen endlose Pakete
                if len(ps.buffer) > 4096:
                    logger.info(f"Discard cyclic to big buffer  data")
                    ps.state = RxState.IDLE
                    ps.buffer.clear()

                continue

            # ---------------------------------------------------
            # COLLECT → Antwort sammeln
            # ---------------------------------------------------
            case RxState.COLLECT:
                #logger.info("RxState.COLLECT")
                result.extend(b)

                if b[0] == 0x0D:
                    logger.info("[DEBUG] generic EndmarkerMessage 0x0D detected ")

                if b == etx:
                    ps.state = RxState.IDLE
                    result.clear()
                    logger.info(f"ETX:Discard collect data in case started without stx byte")
                    print(" #-#-#-# ",end="")
                    continue

                # Marker‑Antwort → Länge erreicht?
                if marker and result.startswith(marker):
                    logger.info("marker startswith -> ok")
                    if len(result) >= num:
                        logger.debug(f"Marker:RX {len(result)} bytes: {result.hex(' ')}")
                        return result
                    
                # Fehlerantwort → beginnt mit "!00CI"
                if wrg_cmd_marker and result.startswith(wrg_cmd_marker):
                    logger.info("wrg_cmd_marker startswith -> ok")
                    if len(result) >= num:
                        err = result[9]  # ASCII '2','4','8'
                        if err == 0x32:
                            logger.info("Err:2: Unknown Command")
                        elif err == 0x34:
                            logger.info("Err:4: Parameter out of allowed range")
                        elif err == 0x38:
                            logger.info("Err:8: Invalid Command in this mode(Check KY)")
                        else:
                            logger.info(f"Unknown Error:{err}")
                        return result

                # ASCII‑Antwort → Struktur prüfen
                if all(c in ASCII_ALLOWED for c in result):
                #if ser.in_waiting==0 and all(c in ASCII_ALLOWED for c in result):

                    if is_ZT(result):
                        text = result.decode("ascii", errors="ignore")
                        data = parse_ZT(text)
                        logger.info(f"ZT: RX {len(result)} bytes: {result.hex(' ')}")
                        logger.info("\n" + data.pretty())
                        return result

                    if is_DA(result):
                        text = result.decode("ascii", errors="ignore")
                        data = parse_DA(text)
                        logger.info(f"DA: RX {len(result)} bytes: {result.hex(' ')}")
                        logger.info("\n" + data.pretty())
                        return result

                    if is_DD(result):
                        text = result.decode("ascii", errors="ignore")
                        data = parse_DD(text)
                        logger.info(f"DD: RX {len(result)} bytes: {result.hex(' ')}")
                        logger.info("\n" + data.pretty())
                        return result

                    if is_DX(result):
                        text = result.decode("ascii", errors="ignore")
                        data = parse_DX(text)
                        logger.info(f"DX: RX {len(result)} bytes: {result.hex(' ')}")
                        logger.info("\n" + data.pretty())
                        return result


                # Wenn zu lang → ungültig
                if len(result) > 256:
                    ps.state = RxState.IDLE
                    result.clear()
                    logger.error(f"Collecting data was not successfull")
                    continue

                continue
