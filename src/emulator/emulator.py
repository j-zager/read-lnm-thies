import serial
import sys
import os
import time
import random
from readLnm.serialRS485 import hex_dump
#Linux
# python3 -m emulator.emulator /dev/pts/4
#socat -d -d pty,raw,echo=0,mode=666 pty,raw,echo=0,mode=666


#Windows
# python3 -m emulator.emulator COM4 
#  

#def run_emulator(port="/dev/pts/4"):
def run_emulator(port="/dev/pts/7"):
    if port is None:
        print(f"No virtual Port available - try to restart")
        return
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

    print(f"Sensor-Emulator läuft auf {port} (9600 8N1)")

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
        cmd = data[2:4].upper()

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

            if cmd == "ZT":
                print("special case: ZT")
                response = f"25.01.05;15:58:10".encode()
            elif cmd == "DA":
                print("special case: DA")
                response = f"-01.6;040.3;02.6;090".encode()
            elif cmd == "DD":
                print("special case: DD")
                response = f"+01;08;1627;4011;2356;235;084;070;-06.4;233;0034;0845;2230".encode()
            elif cmd == "DX":
                print("special case: DX")
                response = f"1;0;0;0;0;0;0;0;0;0;0;0;0;0;1;0".encode()
            else:
                print("normal case")
                response = f"!{dev_id}{cmd}12345".encode()


            traffic = generate_random_traffic_exclusive()
            if traffic is not None:
                ser.write(traffic)
                #ser.flush()
                print("Traffic Antwort gesendet:", repr(traffic))
                #time.sleep(0.02)   # <<< entscheidend für echtes Verhalten


            ser.write(response)
            print(f"Hex:{hex_dump(response)}")
            print("Antwort gesendet:", repr(response))

        else:
            # Ungültige Länge
            print("Ungültige Telegrammlänge → keine Antwort")
            continue

# def generate_random_traffic() -> bytes | None:
#     # 50% Chance: None zurückgeben
#     if random.random() < 0.5:
#         return None

#     # Länge zwischen 15 und 17
#     length = random.randint(15, 17)

#     # 50% Chance: STX am Anfang
#     use_stx = random.random() < 0.5

#     payload_length = length - 1  # ETX kommt immer am Ende

#     if use_stx:
#         payload_length -= 1  # STX belegt ein Byte

#     # Zufällige Bytes erzeugen
#     payload = os.urandom(payload_length)

#     # Nachricht zusammensetzen
#     if use_stx:
#         msg = b"\x02" + payload + b"\x03"
#     else:
#         msg = payload + b"\x03"

#     return msg


def generate_random_traffic_exclusive() -> bytes | None:
    # 50% Chance: None zurückgeben
    if random.random() < 0.01:
        return None

    # Länge zwischen 15 und 17
    total_len = random.randint(15, 17)

    # 50% Chance: STX am Anfang
    use_stx = random.random() < 0.99

    # Verbotene Zeichen
    forbidden = {0x02, 0x03, 0x21}  # STX, ETX, '!'

    # Payload-Länge berechnen
    payload_len = total_len - 1  # ETX am Ende
    if use_stx:
        payload_len -= 1  # STX am Anfang

    payload = generate_payload(payload_len,forbidden)

    # Nachricht zusammensetzen
    if use_stx:
        msg = b"\x02" + payload + b"\x03"
    else:
        msg = payload + b"\x03"

    print(msg.hex(" "))
    return msg

def generate_payload(payload_len, forbidden):
    # 1. Erlaubte Bytes bestimmen
    allowed = []
    for value in range(0x22, 0x7F):  # druckbare ASCII-Zeichen
        if value not in forbidden:
            allowed.append(value)

    # 2. Zufälligen Payload erzeugen
    payload_bytes = []
    for _ in range(payload_len):
        random_byte = random.choice(allowed)
        payload_bytes.append(random_byte)

    # 3. In echtes bytes-Objekt umwandeln
    return bytes(payload_bytes)


def emu():
    port = sys.argv[1] if len(sys.argv) > 1 else None#"/dev/pts/6"
    run_emulator(port)

    
if __name__ == "__main__":
    emu()
