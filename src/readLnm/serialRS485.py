import asyncio
import serial
import serial.tools.list_ports
from generic_utils.io.loggerConfig import getSerialLogger 
import platform
from readLnm.handleVirtualPorts import  smart_select_port


logger = getSerialLogger()

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
   


async def read_bytes_endmarkerOld(
    ser: serial.Serial,
    num: int,
    timeout: float = 1.0,
    endmarker: bytes = b"\x0D\x0A\x03"
) -> bytearray | None:

    if ser is None or not ser.is_open:
        logger.error("read_bytes: port is not opened")
        return None

    if num <= 0:
        logger.error("read_bytes: num must be > 0")
        raise ValueError("num must be > 0")

    end_time = asyncio.get_event_loop().time() + timeout

    buffer = bytearray()      # zum Finden des Endmarkers
    result = bytearray()      # echte Nutzdaten nach dem Marker
    collecting = False        # erst sammeln, wenn Marker gefunden wurde

    try:
        while True:
            # Timeout prüfen
            if asyncio.get_event_loop().time() > end_time:
                logger.warning(f"Timeout while waiting for endmarker or {num} bytes")
                return None

            # Wenn keine Daten da → kurz warten
            if ser.in_waiting == 0:
                await asyncio.sleep(0.001)
                continue

            # Lesen (immer nur 1 Byte, um Marker sicher zu erkennen)
            chunk = ser.read(1)
            if not chunk:
                continue

            # logger.debug(f"RX 1 byte: {chunk.hex(' ')}")

            # Noch nicht im Sammelmodus → nach Endmarker suchen
            if not collecting:
                buffer.extend(chunk)

                # Endmarker erkannt?
                if buffer.endswith(endmarker):
                    logger.info("Endmarker erkannt – beginne Nutzdaten zu sammeln")
                    collecting = True
                    buffer.clear()  # alles davor verwerfen
                continue

            # Ab hier sammeln wir echte Nutzdaten
            result.extend(chunk)

            # Genug Bytes gesammelt?
            if len(result) >= num:
                # logger.info(f"Received full response ({len(result)} bytes)")
                logger.debug(f"RX {len(result)} bytes: {result.hex(' ')}")
                return result

    except Exception as e:
        logger.error(f"Receiving error:{e}")
        return bytearray()


# async def read_bytes_endmarker(
#     ser: serial.Serial,
#     num: int,
#     timeout: float = 1.0,
#     endmarker: bytes = b"\x0D\x0A\x03"
# ) -> bytearray | None:

#     if ser is None or not ser.is_open:
#         logger.error("read_bytes: port is not opened")
#         return None

#     if num <= 0:
#         logger.error("read_bytes: num must be > 0")
#         raise ValueError("num must be > 0")

#     end_time = asyncio.get_event_loop().time() + timeout

#     buffer = bytearray()      # zum Finden des Endmarkers
#     result = bytearray()      # echte Nutzdaten
#     collecting = False        # erst sammeln, wenn Marker ODER Nutzdaten kommen

#     try:
#         while True:
#             # Timeout
#             if asyncio.get_event_loop().time() > end_time:
#                 logger.warning("Timeout while reading")
#                 return None

#             if ser.in_waiting == 0:
#                 await asyncio.sleep(0.001)
#                 continue

#             b = ser.read(1)
#             if not b:
#                 continue

#             # logger.debug(f"RX 1 byte: {b.hex(' ')}")

#             # Wenn wir noch nicht sammeln → prüfen ob Endmarker kommt
#             if not collecting:
#                 buffer.extend(b)

#                 # Endmarker gefunden → Sammelmodus aktivieren
#                 if buffer.endswith(endmarker):
#                     logger.info("Endmarker erkannt – beginne Nutzdaten zu sammeln")
#                     collecting = True
#                     buffer.clear()
#                     continue

#                 # Wenn Daten kommen, die NICHT zum Endmarker gehören → sofort sammeln
#                 if len(buffer) > len(endmarker):
#                     logger.info("Keine zyklische Nachricht – beginne sofort zu sammeln")
#                     collecting = True
#                     result.extend(buffer)
#                     buffer.clear()
#                     continue

#                 continue

#             # Ab hier sammeln wir echte Nutzdaten
#             result.extend(b)

#             if len(result) >= num:
#                 logger.debug(f"RX {len(result)} bytes: {result.hex(' ')}")
#                 return result

#     except Exception as e:
#         logger.error(f"Receiving error: {e}")
#         return None


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
        logger.error("read_bytes: num must be > 0")
        raise ValueError("num must be > 0")

    end_time = asyncio.get_event_loop().time() + timeout

    buffer = bytearray()      # zum Finden von STX/ETX
    result = bytearray()      # echte Nutzdaten
    in_cyclic = False         # sind wir gerade in einer zyklischen Nachricht?
    collecting = False        # sammeln wir Nutzdaten?

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

            # Noch nicht im Sammelmodus → prüfen auf STX/ETX
            if not collecting:
                buffer.extend(b)

                # STX erkannt → wir sind in einer zyklischen Nachricht
                if buffer.endswith(stx):
                    in_cyclic = True
                    buffer.clear()
                    continue

                # ETX erkannt → zyklische Nachricht zu Ende
                if in_cyclic and buffer.endswith(etx):
                    in_cyclic = False
                    buffer.clear()
                    continue

                # Wenn wir NICHT in einer zyklischen Nachricht sind
                # und Daten kommen → das ist die Antwort
                if not in_cyclic and len(buffer) >= 1:
                    collecting = True
                    result.extend(buffer)
                    buffer.clear()
                    continue

                continue

            # Ab hier sammeln wir echte Nutzdaten
            result.extend(b)

            if len(result) >= num:
                logger.debug(f"RX {len(result)} bytes: {result.hex(' ')}")
                return result

    except Exception as e:
        logger.error(f"Receiving error: {e}")
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


  