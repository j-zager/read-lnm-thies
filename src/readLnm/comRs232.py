import asyncio
import serial
import serial_asyncio

from generic_utils.comm import comAsyncioSerialRS232
from generic_utils.io.loggerConfig import getLogger

logger = getLogger("ThiesLNM comm log")

async def sender(writer):
    while True:
        await comAsyncioSerialRS232.sendBytesAsync(writer, bytearray(b"00SV\r"))
        await asyncio.sleep(1.0)

async def receiver(reader):
    while True:
        data = await comAsyncioSerialRS232.receiveBytesAsync(reader, 10, timeout=1.0)
        if data:
            logger.info("RX:", data)
        else:
            logger.debug("Timeout")
        await asyncio.sleep(0)

async def main():
    reader, writer = await comAsyncioSerialRS232.initSerialRS232Async(
        "COM1",
        9600,
        serial.EIGHTBITS,
        serial.PARITY_EVEN,
        serial.STOPBITS_ONE
    )

    task1 = asyncio.create_task(sender(writer))
    task2 = asyncio.create_task(receiver(reader))

    await asyncio.gather(task1, task2)


async def do_single_request(msg: bytes = b"00SV\r"):

    # 0. SET oder READ?
    is_set = (len(msg) == 10)
    expects_response = not is_set

    # 1. Port öffnen
    reader, writer = await comAsyncioSerialRS232.initSerialRS232Async(
        # port="COM1", # Windows
        port="proxy:/dev/pts/4", #Linux
        baudrate=9600,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_EVEN,
        stopbits=serial.STOPBITS_ONE
    )

    if reader is None:
        logger.error("Port konnte nicht geöffnet werden")
        return

    # 2. Nachricht senden
    ok = await comAsyncioSerialRS232.sendBytesAsync(writer, bytearray(msg))

    if not ok:
        logger.error("Senden fehlgeschlagen")
        await comAsyncioSerialRS232.closeAllPorts({"COM1": (reader, writer)})
        return

    # 3. Antwort empfangen (z. B. 10 ASCII-Zeichen)
    response = None
    if expects_response:
        response = await comAsyncioSerialRS232.receiveBytesAsync(
            reader,
            numBytes=10,
            timeout=1.0
        )

        if response:
            logger.info(f"RX ← {response.hex(' ')}  ASCII: {response.decode(errors='ignore')}")
        else:
            logger.warning("Timeout oder keine Antwort (obwohl erwartet!)")
    else:
        logger.info("SET-Befehl → keine Antwort erwartet")

    # 4. Port schließen
    await comAsyncioSerialRS232.closeAllPorts({"COM1": (reader, writer)})

def build_message(
    command: str,
    device_id: int = 0,
    value: int | None = None
) -> bytes:
    """
    Baut ein Telegramm nach dem Format:
    <id><BB><ppppp><CR>

    - id: 2-stellig, führende Nullen
    - BB: Befehlscode (2 Zeichen)
    - ppppp: optionaler Parameter, 5-stellig, führende Nullen
    """

    # ID immer 2-stellig
    id_str = f"{device_id:02d}"

    # Command immer 2 Zeichen, uppercase
    cmd_str = command.upper()

    # Parameter optional
    if value is None:
        msg = f"{id_str}{cmd_str}\r"
    else:
        msg = f"{id_str}{cmd_str}{value:05d}\r"

    return msg.encode("ascii")