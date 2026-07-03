import serial
from readLnm.myLogger import get_logger, setup_logger

logger = get_logger(__name__)

def read(port="/dev/ttyACM0"):
        # Logger JETZT konfigurieren
    setup_logger(
        debug_mode=True,
        logfile_name="Sniffer_protocol_climate_LNM_Thies.log"
    )

    try: 
        par=serial.PARITY_NONE
        #parity=serial.PARITY_EVEN
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

    print(f"Nur Reader läuft auf {port} (9600 {par})")
    response = bytearray()

    while True:
        b = ser.read(1)
        if not b:
            continue
        response.extend(b)
        # Prüfen auf STX (0x02)
        if b == b'\x02':
            print("STX (0x02) empfangen")

        # Prüfen auf ETX (0x03)
        if b == b'\x03':
            print("ETX (0x03) empfangen")
            logger.debug(f"RX ← {response.hex(' ')}")
            logger.debug(f"ASCII: {response.decode(errors='ignore')}")
            response.clear()

        #print(f"RX ← {b.hex(' ')}  ASCII: {b.decode(errors='ignore')}")
        logger.debug(f"RX ← {b.hex(' ')}  ASCII: {b.decode(errors='ignore')}")



    
if __name__ == "__main__":
    read()