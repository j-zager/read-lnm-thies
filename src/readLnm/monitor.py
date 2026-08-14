import serial
from readLnm.myLogger import get_logger, setup_logger

logger = get_logger(__name__)

def monitor(port="/dev/ttyACM0"):
        # Logger JETZT konfigurieren
    setup_logger(
        debug_mode=True,
        logfile_name="Sniffer_protocol_climate_LNM_Thies.log"
    )

    try: 
        par=serial.PARITY_NONE #read sensor bootlader data
        #par=serial.PARITY_EVEN
        ser = serial.Serial(
            port,
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=par,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
    except FileNotFoundError:
        print(f"Port {port} does not exist.")  
        return None  
    except PermissionError:
        print(f"Access of port {port} denied")  
        return None  
    except serial.SerialException as e:
        print(f"SerialException while open port {port}:{e}")  
        return None  
    except Exception as error:
        print(f"Unknown error at {port}: {repr(error)}")
        return None

    print(f"Monitor runs at {port} (9600 {par})")
    response = bytearray()

    while True:
        b = ser.read(1)
        if not b:
            continue
        response.extend(b)
        # Prüfen auf STX (0x02)
        if b == b'\x02':
            print("STX (0x02) received")

        # Prüfen auf ETX (0x03)
        elif b == b'\x03':
            print("ETX (0x03) received")
            logger.debug(f"RX ← {response.hex(' ')}")
            logger.debug(f"ASCII: {response.decode(errors='ignore')}")
            response.clear()



        elif b == b'\x10':
            print("Short TLS telegramm start indication (0x10 received")

        elif b == b'\x68':
            print("Long TLS telegramm start indication (0x68) received")

        elif b == b'\x16':
            print("General TLS telegramm termination indication (0x16) received")

        elif b == b'\xE5':
            print("TLS telegramm Acknowledge indication (0xE5) received")

        #print(f"RX ← {b.hex(' ')}  ASCII: {b.decode(errors='ignore')}")
        logger.debug(f"RX ← {b.hex(' ')}  ASCII: {b.decode(errors='ignore')}")



    
if __name__ == "__main__":
    monitor()