import asyncio
import serial
import serial.tools.list_ports
import platform
from readLnm.handleVirtualPorts import  smart_select_port
from readLnm.myLogger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------
# 1. Ports finden
# ---------------------------------------------------------
def find_serial_ports() -> list[str]:
    ports = [p.device for p in serial.tools.list_ports.comports()]
    logger.debug(f"Found Ports: {ports}")
    return ports


# ---------------------------------------------------------
# 2. Port öffnen (mit Sicherheitschecks)
# ---------------------------------------------------------
def open_port(  port: str = "COM1",
                baudrate: int = 9600,
                bytesize: int = serial.EIGHTBITS,
                stopbits: int = serial.STOPBITS_ONE,
                parity: str = serial.PARITY_NONE,
                ) -> serial.Serial|None:
    if not isinstance(port, str):
        logger.error("open_port:Port has to be a string")
        raise ValueError("Port has to be a string")

    try:
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=0,
            write_timeout=1.0
        )
        logger.info(f"successfully opened: {port}")
        return ser

    except FileNotFoundError:
        logger.error(f"Port {port} does not exist.")  
        return None  
    except PermissionError:
        logger.error(f"Access of port {port} denied")  
        return None  
    except serial.SerialException as e:
        logger.error(f"SerialException while open port {port}:{e}")  
        return None  
    except Exception as error:
        logger.error(f"Unknown error at {port}: {repr(error)}")
        return None

# ---------------------------------------------------------
# 3. Ports schließen
# ---------------------------------------------------------
def close_all_ports(connections: dict[str, serial.Serial]):
    for port, ser in connections.items():
        try:
            if ser and ser.is_open:
                ser.close()
                logger.info(f"port closed: {port}")
            else:
                logger.debug(f"port {port} was closen")
        except Exception as e:
            logger.error(f"Error at closing {port}: {e}")


# ---------------------------------------------------------
# 4. Bytes senden (async, sicher)
# ---------------------------------------------------------
async def send_bytes(ser: serial.Serial, data: bytes) -> bool:
    if ser is None or not ser.is_open:
        logger.error("send_bytes: port is not opened")
        return False

    if not isinstance(data, (bytes, bytearray)):
        logger.error("send_bytes: sendData muss bytes oder bytearray sein")
        raise ValueError("send_bytes expects bytes or bytearray")

    try:
        written = ser.write(data)
        if written != len(data):
            logger.error(f"Only {written}/{len(data)} bytes were written")
            return False
        else:
            logger.debug(f"Send ({len(data)} Bytes): {data.hex(' ')}")
        
    except serial.SerialTimeoutException as e:
        logger.error(f"Send error (timeout): {e}")
        return False

    except serial.SerialException as e:
        logger.error(f"Send error (serial exception): {e}")
        return False

    except OSError as e:
        logger.error(f"Send error (OS error): {e}")
        return False

    except ValueError as e:
        logger.error(f"Send error (invalid value): {e}")
        return False

    except TypeError as e:
        logger.error(f"Send error (type error): {e}")
        return False

    except Exception as e:
        logger.error(f"Send error (unknown exception): {e}")
        return False


    try:
        ser.flush()
    except serial.SerialException as e:
        logger.error(f"Flush error (serial exception): {e}")
        return False
    except OSError as e:
        logger.error(f"Flush error (OS error): {e}")
        return False
    except Exception as e:
        logger.error(f"Flush error (unknown exception): {e}")
        return False

    await asyncio.sleep(0)
    return True


# ---------------------------------------------------------
# 5. Bytes lesen (async, mit Timeout & Sicherheitschecks)
# ---------------------------------------------------------
async def read_bytes(ser: serial.Serial, num: int, timeout: float = 1.0)->bytearray|None:
    if ser is None or not ser.is_open:
        logger.error("read_bytes: port is not opened")
        return None

    if num <= 0:
        logger.error("read_bytes: num must be > 0 ")
        raise ValueError("num must be > 0")

    end_time = asyncio.get_event_loop().time() + timeout
    buffer = bytearray()

    try:
        while len(buffer) < num:
            chunk = ser.read(num - len(buffer))

            if chunk:
                buffer.extend(chunk)
                logger.debug(f"RX {len(chunk)} bytes: {chunk.hex(' ')}")

            if asyncio.get_event_loop().time() > end_time:
                logger.warning(f"Timeout while reading {num} bytes")
                return None

            await asyncio.sleep(0.001)

        logger.info(f"Received full response ({len(buffer)} bytes)")
        return bytearray(buffer)

    except Exception as e:
        logger.error(f"Receiving error:{e}")
        return bytearray()
   


async def read_bytes_marker(
    ser: serial.Serial,
    num: int,
    timeout: float = 1.0,
    stx: bytes = b"\x02",
    etx: bytes = b"\x03",
) -> bytearray | None:

    if ser is None or not ser.is_open:
        logger.error("read_bytes: port is not opened")
        return None

    if num <= 0:
        raise ValueError("num must be > 0")

    end_time = asyncio.get_event_loop().time() + timeout

    result = bytearray()
    in_cyclic = False
    cyclic_buffer = bytearray()

    try:
        while True:
            # Timeout
            if asyncio.get_event_loop().time() > end_time:
                logger.warning("Timeout while reading")
                return None

            if ser.in_waiting == 0:
                await asyncio.sleep(0.001)
                continue

            b = ser.read(1)
            if not b:
                continue

            # -------------------------------
            # 1) Zyklische Nachricht erkennen
            # -------------------------------
            if not in_cyclic:
                # Start eines zyklischen Pakets?
                if b == stx:
                    in_cyclic = True
                    cyclic_buffer.clear()
                    cyclic_buffer.extend(b)
                    continue

                # Normale Nutzdaten → sammeln
                result.extend(b)

                if len(result) >= num:
                    logger.debug(f"RX {len(result)} bytes: {result.hex(' ')}")
                    return result

            else:
                # Wir sind in einer zyklischen Nachricht
                cyclic_buffer.extend(b)

                # Ende erkannt?
                if b == etx:
                    # Zyklisches Paket komplett → verwerfen
                    in_cyclic = False
                    cyclic_buffer.clear()
                    continue

                # Falls zyklisches Paket extrem groß wird → Schutz
                if len(cyclic_buffer) > 4096:
                    logger.warning("Cyclic packet too large, discarding")
                    in_cyclic = False
                    cyclic_buffer.clear()
                    continue

    except Exception as e:
        logger.error(f"Receiving error: {e}")
        return None


async def read_response(
    ser: serial.Serial,
    num: int,
    marker: bytes | None = None,   # z.B. b"!wxyz"
    timeout: float = 1.0,
    stx: int = 0x02,
    etx: int = 0x03,
) -> bytearray | None:

    if ser is None or not ser.is_open:
        return None

    end_time = asyncio.get_event_loop().time() + timeout

    STATE_IDLE = 0
    STATE_CYCLIC = 1
    STATE_COLLECT = 2

    state = STATE_IDLE
    result = bytearray()
    cyclic_buf = bytearray()

    # ASCII‑Startzeichen
    ascii_starts = b"+-0123456789"

    try:
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

            # ---------------------------------------------------------
            # STATE: CYCLIC → verwerfen bis ETX
            # ---------------------------------------------------------
            if state == STATE_CYCLIC:
                cyclic_buf.append(byte)

                # Zyklusende
                if byte == etx:
                    state = STATE_IDLE
                    cyclic_buf.clear()
                # Schutz gegen endlose Pakete
                elif len(cyclic_buf) > 4096:
                    state = STATE_IDLE
                    cyclic_buf.clear()

                continue

            # ---------------------------------------------------------
            # STATE: IDLE → Startzeichen suchen
            # ---------------------------------------------------------
            if state == STATE_IDLE:

                # Zyklisches Paket beginnt
                if byte == stx:
                    state = STATE_CYCLIC
                    cyclic_buf.clear()
                    continue

                # Marker‑Antwort beginnt
                if byte == ord("!"):
                    result = bytearray(b"!")
                    state = STATE_COLLECT
                    continue

                # ASCII‑Antwort beginnt
                if byte in ascii_starts:
                    result = bytearray(b)
                    state = STATE_COLLECT
                    continue

                # Müll → ignorieren
                continue

            # ---------------------------------------------------------
            # STATE: COLLECT → Antwort sammeln
            # ---------------------------------------------------------
            if state == STATE_COLLECT:
                result.extend(b)

                if len(result) >= num:
                    return result

                continue

    except Exception:
        return None





def hex_dump(data: bytes) -> str:
    """Gibt einen formatierten Hexdump zurück."""
    if not data:
        return "<empty>"

    hex_part = " ".join(f"{b:02x}" for b in data)
    ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in data)

    return f"{hex_part}   |{ascii_part}|"

def get_default_port()->str:
    if platform.system() == "Windows":
        return "COM1"
    else:
        return "/dev/ttyACM0"
        # return "/dev/pts/4"   # oder dynamisch ermitteln

def request_port()->str:
    if platform.system() == "Windows":
        portUser = input("Port eingeben (z.B. COM1 ): ")
        return portUser
    else:
        #portUser = input("Port eingeben (z.B. /dev/pts/4): ")
        portUser = input("Port eingeben (z.B. /dev/ttyACM1): ")
        return portUser
    
def choose_serial_port() -> str | None:
    ports = find_serial_ports()

    if not ports:
        logger.error("No serial ports detected")
        return None
    # elif (len(ports)==1):
    #     logger.info("one available port:{ports[0]} is taken.")
    #     return ports[0]

    print("Available serial ports:")
    for idx, port in enumerate(ports):
        print(f"  [{idx}] {port}")

    while True:
        user_input = input("Select port index: ").strip()

        # Check if input is a number
        if not user_input.isdigit():
            print("Please enter a valid number")
            continue

        index = int(user_input)

        # Check if index is in range
        if 0 <= index < len(ports):
            selected = ports[index]
            logger.info(f"User selected port: {selected}")
            return selected
        else:
            print("Index out of range, try again")


def flush_serial(ser: serial.Serial):
    ser.reset_input_buffer()   # Linux/Windows: löscht OS-Puffer
    ser.reset_output_buffer()


  