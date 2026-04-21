import serial
import sys

def run_emulator(port="/dev/pts/5"):
    ser = serial.Serial(
        port,
        baudrate=9600,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_EVEN,
        stopbits=serial.STOPBITS_ONE,
        timeout=1
    )

    print(f"Sensor-Emulator läuft auf {port} (9600 8E1)")

    buffer = ""

    while True:
        ch = ser.read(1).decode(errors="ignore")

        if not ch:
            continue

        # Zeichen sammeln
        buffer += ch

        # Erst reagieren, wenn CR empfangen wurde
        if ch != "\r":
            continue

        # CR empfangen → Telegramm vollständig
        data = buffer.strip()  # entfernt CR
        buffer = ""            # Buffer zurücksetzen

        print(f"Empfangen: {repr(data)}")

        # Mindestlänge prüfen
        if len(data) < 4:
            print("Ungültiges Telegramm → keine Antwort")
            continue

        # ID = 2 Zeichen
        dev_id = data[0:2]

        # CMD = 2 Zeichen
        cmd = data[2:4]

        # SET-Befehl? (ID + CMD + PARAM + CR → 10 Zeichen)
        # data enthält KEIN \r mehr, daher:
        # READ = 4 Zeichen
        # SET  = 9 Zeichen
        if len(data) == 9:
            # SET-Befehl
            param = data[4:9]
            print(f"Settings successful for device {dev_id}, command {cmd} with parameter {param}")
            # WICHTIG: KEINE Antwort senden
            continue

        elif len(data) == 4:
            # READ-Befehl → Antwort senden
            response = f"{dev_id}{cmd}12345\r".encode()
            ser.write(response)
            print("Antwort gesendet:", repr(response))

        else:
            # Ungültige Länge
            print("Ungültige Telegrammlänge → keine Antwort")
            continue

def emu():
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/pts/6"
    run_emulator(port)
    
if __name__ == "__main__":
    emu()
