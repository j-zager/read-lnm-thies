import serial
from readLnm.serialRS485 import open_port,send_bytes,read_bytes,read_bytes_marker,close_all_ports,choose_serial_port, flush_serial
from readLnm.commands import get_rx_len_from_msg
from generic_utils.io.loggerConfig import getSerialLogger 
from readLnm.handleVirtualPorts import init_virtual_port_selection


logger = getSerialLogger()

async def do_single_message(msg: bytes = b"00SV\r",port:int=None):

    # PTYs (socat) cannot handle parity
    if "/dev/pts/" in port:
        logger.info("Detected PTY → using PARITY_NONE for testing")
        par = serial.PARITY_NONE

    # Real hardware → use EVEN parity
    else:
        logger.info("Detected real serial device → using PARITY_EVEN")
        #par = serial.PARITY_EVEN
        par = serial.PARITY_NONE
        logger.warning("Detected real serial device → using PARITY_NONE because of old device configuration")

    if port is None:
        return
    

    # 0. SET oder READ?
    is_set = (len(msg) == 10)
    expects_response = not is_set

    # 1. Port öffnen
    ser = open_port(port=port,
                    baudrate=9600,
                    bytesize=serial.EIGHTBITS,
                    parity=par,
                    stopbits=serial.STOPBITS_ONE)

    if ser is None:
        logger.error("Port could not be opened")
        return
    
    flush_serial(ser=ser)

    # 2. Nachricht senden
    ok = await send_bytes(ser=ser, data=bytearray(msg))

    if not ok:
        logger.error("Sending was not successfull")
        await close_all_ports({port:ser})
        return
    
    logger.info(f"TX → {bytearray(msg).hex(' ')}  ASCII: {bytearray(msg).decode(errors='ignore')}")

    # 3. Antwort empfangen (z. B. 10 ASCII-Zeichen)
    rxChexpected = get_rx_len_from_msg(msg)
    response = None
    if expects_response:
        # response = await read_bytes(ser=ser, num = 10, timeout = 1.0)
        # response = await read_bytes(ser=ser, num = rxChexpected, timeout = 1.0)
        # remove message ending with CR LF ETX - b"\x0D\x0A\x03"
        response = await read_bytes_endmarker(ser=ser, num = rxChexpected, timeout = 1.0,endmarker=b"\x0D\x0A\x03")

        if response:
            logger.info(f"RX ← {response.hex(' ')}  ASCII: {response.decode(errors='ignore')}")
        else:
            logger.warning("Timeout or no responsive (response was expected!)")
    else:
        logger.info("SET Command → No response expected")

    # 4. Port schließen
    close_all_ports({port:ser})


def portSelection()->str:
    virtualPort = init_virtual_port_selection()
    if virtualPort is None:
        port = choose_serial_port()
    else:
        #port = "/dev/pts/4" 
        port = virtualPort
    logger.info(f"used Port{port}")
    return port