import serial

def read(port="/dev/ttyACM0"):

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

    print(f"Nur Reader läuft auf {port} (9600 {par})")

    while True:
        b = ser.read(1)
        if not b:
            continue

        # Prüfen auf STX (0x02)
        if b == b'\x02':
            print("STX (0x02) empfangen")

        # Prüfen auf ETX (0x03)
        if b == b'\x03':
            print("ETX (0x03) empfangen")

        print(f"RX ← {b.hex(' ')}  ASCII: {b.decode(errors='ignore')}")



    
if __name__ == "__main__":
    read()