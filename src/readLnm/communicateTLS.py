import time
import serial

from enum import Enum, auto

PORT = "/dev/ttyACM0"  # Oder "/dev/ttyUSB0"
DEVICE_ALL = 0xFF
DEVICE_ID = 0       # Deine ID = 0

# Timing-Konstanten nach TLS-Spezifikation (in Sekunden)
TAP = 0.120  # 120 ms Antwortüberwachungszeit der Primary
TWP = 0.050  # 50 ms Mindestwartezeit der Primary vor dem nächsten Senden

class TlsState(Enum):
    INIT = auto()
    SEND_RQS = auto()
    SEND_RES0 = auto()
    WAIT_FOR_RR = auto()
    RESTART_PROCESS = auto()
    FINISH_PROCESS = auto()
    WAIT_FOR_S1_START = auto()
    WAIT_FOR_S1_HEADER = auto()
    WAIT_FOR_S1_FRAME = auto()


def reverse_bits_mathematisch(b: int) -> int:
    ergebnis = 0
    for _ in range(8):
        ergebnis = (ergebnis << 1) | (b & 1)
        b >>= 1
    return ergebnis


# def reverse_bits(b: int) -> int:
#     """Spiegelt die Bits eines einzelnen Bytes komplett um (LSB <-> MSB)."""
#     # Verwandelt z.B. 01101000 (0x68) in 00010110 (0x16)
#     return int('{:08b}'.format(b)[::-1], 2)

def reverse_bits(b: int) -> int:
    """
    Spiegelt die Bits eines einzelnen Bytes komplett um (LSB <-> MSB).
    Beispiel: Das Byte 0x68 wird zu 0x16.
    """
    # 1. Schritt: Wandle die Zahl in einen Text aus Nullen und Einsen um.
    # ':08b' sorgt dafür, dass der Text IMMER genau 8 Zeichen lang ist (Auffüllen mit Nullen).
    # Aus der Zahl 0x68 (dezimal 104) wird hier der Text: "01101000"
    binaer_text = '{:08b}'.format(b)
    
    # 2. Schritt: Drehe den Text von hinten nach vorne um.
    # Das [[::-1]] liest den String rückwärts (Schrittweite -1).
    # Aus dem Text "01101000" wird hier der Text: "00010110"
    #text[START : STOPP : SCHRITTWEITE]
    #binaer_text[  :  : -1 ]
    #            ▲  ▲   ▲
    #            │  │   └── Schrittweite ist -1 (rückwärts gehen)
    #           │  └────── Stopp ist leer (bis zum logischen Ende)
    #          └───────── Start ist leer (beim logischen Anfang beginnen)

    umgedrehter_text = binaer_text[::-1]
    
    # 3. Schritt: Wandle den umgedrehten Binär-Text zurück in eine echte Zahl.
    # Die Option ', 2' sagt Python, dass es sich um eine Binärzahl (Basis 2) handelt.
    # Aus dem Text "00010110" wird die Zahl 22, was in Hexadezimal exakt 0x16 ist.
    ergebnis_zahl = int(umgedrehter_text, 2)
    
    # 4. Schritt: Gib die fertige, bit-gespiegelte Zahl zurück.
    return ergebnis_zahl


def unmirror_response_bytes(raw_mirrored_bytes: bytes) -> bytes:
    """
    Nimmt die gespiegelten Empfangsbytes vom RS485-Wandler entgegen,
    dreht die Bits in jedem einzelnen Byte wieder um (MSB <-> LSB)
    und gibt das korrekte Klartext-Bytearray für den Parser zurück.
    """
    # 1. Schritt: Erstelle eine leere Liste, um die korrigierten Zahlen zu sammeln
    klartext_zahlen_liste = []
    
    # 2. Schritt: Gehe in einer klassischen Schleife jedes gespiegelte Byte einzeln durch
    for b in raw_mirrored_bytes:
        
        # 3. Schritt: Wandle das aktuelle Byte in einen 8 Zeichen langen Binärtext um.
        # Aus dem gespiegelten Sensor-Byte 0x16 wird hier der Text: "00010110"
        binaer_text = '{:08b}'.format(b)
        
        # 4. Schritt: Spiegele den Binärtext rückwärts (über den Slicing-Operator [::-1]).
        # Aus dem Text "00010110" wird wieder das Original: "01101000"
        original_text = binaer_text[::-1]
        
        # 5. Schritt: Wandle den originalen Binärtext zurück in eine Ganzzahl (Basis 2).
        # Aus dem Text "01101000" berechnet Python die Zahl 104 (was Hexadezimal 0x68 entspricht).
        original_zahl = int(original_text, 2)
        
        # 6. Schritt: Hänge die korrigierte Zahl an unsere Sammel-Liste an
        klartext_zahlen_liste.append(original_zahl)
        
    # 7. Schritt: Verwandle die fertige Zahlenliste in ein echtes Python-Byte-Objekt
    return bytes(klartext_zahlen_liste)




def build_ft12_telegram(control_byte: int, addr: int, user_data: bytes = b"") -> bytes:
    """Erzeugt ein mathematisch exaktes TLS FT1.2 Telegramm."""
    protected_area = bytes([control_byte, addr]) + user_data
    length = len(protected_area)
    cs = sum(protected_area) & 0xFF

    # Das normale Standard-Telegramm generieren
    normal_telegram = bytes([0x68, length, length, 0x68]) + protected_area + bytes([cs, 0x16])
    
    # # JETZT: Jedes Byte bitweise umdrehen für die TLS-Leitungs-Reihenfolge
    # #mirrored_bytes = [reverse_bits(b) for b in normal_telegram]

    # # 1. Schritt: Erstelle eine leere Liste, in der wir die gespiegelten Bytes sammeln.
    # mirrored_bytes_liste = []

    # # 2. Schritt: Starte eine klassische Schleife.
    # # Wir gehen nacheinander jedes einzelne Byte aus dem normalen Telegramm durch.
    # for b in normal_telegram:
        
    #     # 3. Schritt: Rufe die Umdreh-Funktion für das EINE aktuelle Byte auf.
    #     # Das Ergebnis (die umgedrehte Zahl) speichern wir kurz zwischen.
    #     umgedrehtes_einzel_byte = reverse_bits(b)
        
    #     # 4. Schritt: Hänge das umgedrehte Byte hinten an unsere Sammel-Liste an.
    #     mirrored_bytes_liste.append(umgedrehtes_einzel_byte)

    # # Am Ende verwandeln wir die Liste wieder in ein echtes Python 'bytes'-Objekt.
    # mirrored_bytes = bytes(mirrored_bytes_liste)
    # # print(mirrored_bytes.hex(' ').upper())
    # # return mirrored_bytes
    print(normal_telegram.hex(' ').upper())
    return normal_telegram

def run_tls_state_machine(ser_conn: serial.Serial, target_addr: int, search_address: bool) -> bool:
    """
    Führt das TLS-Anlaufverfahren als zeitgesteuerte State Machine aus.
    Optimiert mit 1-Millisekunden-Takt zur perfekten Balance aus CPU-Schonung
    und exakter Einhaltung des TLS-Timings.
    """
    state = TlsState.INIT
    current_id = 0
    is_scan_mode = search_address
    last_send = 0.0
    success = False
    raw_receive_buffer = b""
    clear_receive_buffer = b""

    # --- HIER DIE HILFSFUNKTION DEFINIEREN ---
    def reset_buffers_and_timer():
        nonlocal clear_receive_buffer, raw_receive_buffer, last_send
        clear_receive_buffer = b""
        raw_receive_buffer = b""
        last_send = time.time()  # nutzt direkt das aktuelle 'now' via time.time()
        ser_conn.reset_input_buffer()  # Schadet nie, das hier direkt mitzuerledigen!


    print(f"\n*** Starte TLS State Machine (Scan-Modus: {is_scan_mode}, Start-Ziel-ID: {target_addr}) ***")

    while True:
        now = time.time()

        # --- ASYNCHRONER EINLESE-TEIL (SCHLEIFENKOPF) ---
        # Liest im 1-ms-Takt ein – exakt abgestimmt auf die Zeichengeschwindigkeit bei 9600 Baud
        if ser_conn.in_waiting > 0:
            bytes_waiting = ser_conn.in_waiting
            new_raw_bytes = ser_conn.read(bytes_waiting)
            raw_receive_buffer += new_raw_bytes
            
            # new_clear_bytes = unmirror_response_bytes(new_raw_bytes)
            new_clear_bytes = raw_receive_buffer
            clear_receive_buffer += new_clear_bytes
            print(f"  [Leitungs-Event] Empfangen: {bytes_waiting} Bytes | Raw: {new_raw_bytes.hex().upper()} | Klar: {new_clear_bytes.hex().upper()}")

        # --- SWITCH-CASE STRUKTUR VIA MATCH-CASE ---
        match state:
            
            case TlsState.INIT:
                if is_scan_mode:
                    current_id = 1
                    print("  [State: INIT] Scan-Flag aktiv. Starte Adress-Suche bei ID 1.")
                else:
                    current_id = target_addr
                    print(f"  [State: INIT] Fix-ID Modus aktiv. Ziel-Adresse eingestellt auf ID {current_id}.")
                state = TlsState.SEND_RQS

            case TlsState.SEND_RQS:
                # Die 50ms-Sperre (Twp) schützt das Senden hier direkt vor JEDEM Durchlauf
                if (now - last_send) >= TWP:
                    telegramm = build_ft12_telegram(control_byte=0x49, addr=current_id)
                    print(f"\n  [State: SEND_RQS] Sende RQS (0x49) an ID {current_id}...")
                    
                    ser_conn.reset_input_buffer()
                    raw_receive_buffer = b""
                    clear_receive_buffer = b""
                    
                    ser_conn.write(telegramm)
                    ser_conn.flush()
                    last_send = now
                    state = TlsState.WAIT_FOR_S1_START


            # =================================================================
            # SUB-STATE 1: Start-Byte finden (Reinigung)
            # =================================================================
            case TlsState.WAIT_FOR_S1_START:
                # Timeout läuft übergeordnet für die gesamte S1-Phase
                if (now - last_send) >= TAP:
                    print(f"  [Timeout] ID {current_id} antwortet nicht.")
                    clear_receive_buffer = b""
                    raw_receive_buffer = b""
                    last_send = now
                    if is_scan_mode: 
                        state = TlsState.RESTART_PROCESS 
                    else: 
                        state = TlsState.FINISH_PROCESS
                    
                elif len(clear_receive_buffer) > 0:
                    if clear_receive_buffer[0] == 0x68:
                        # Startzeichen gefunden! Weiter zum Header
                        print("Found start sign 0x68")
                        state = TlsState.WAIT_FOR_S1_HEADER
                    else:
                        # Müll wegschneiden, Hauptschleife liest im nächsten Takt weiter
                        print(f"trash data{clear_receive_buffer[0]}")
                        clear_receive_buffer = clear_receive_buffer[1:]

            # =================================================================
            # SUB-STATE 2: Header validieren (4 Bytes)
            # =================================================================
            case TlsState.WAIT_FOR_S1_HEADER:
                if (now - last_send) >= TAP:
                    clear_receive_buffer = b""
                    raw_receive_buffer = b""
                    last_send = now

                    if is_scan_mode: 
                        state = TlsState.RESTART_PROCESS
                    else:
                        state = TlsState.FINISH_PROCESS
                     
                elif len(clear_receive_buffer) >= 4:
                    if clear_receive_buffer[3] == 0x68:
                        # Header ist gültig (Byte 0 und 3 sind 0x68). Weiter zum Rest des Rahmens.
                        print("Header is valid:buffer[3] = 0x68")
                        state = TlsState.WAIT_FOR_S1_FRAME
                    else:
                        # Fehlalarm (Rauschen). Erstes Byte verwerfen und neu nach Start suchen.
                        clear_receive_buffer = clear_receive_buffer[1:]
                        print("Error at header!")
                        state = TlsState.WAIT_FOR_S1_START

            # =================================================================
            # SUB-STATE 3: Ganzen Rahmen einlesen & Checksumme prüfen
            # =================================================================
            case TlsState.WAIT_FOR_S1_FRAME:
                if (now - last_send) >= TAP:
                    clear_receive_buffer = b""
                    raw_receive_buffer = b""
                    last_send = now
                    if is_scan_mode: 
                        state = TlsState.RESTART_PROCESS
                    else:
                        state = TlsState.FINISH_PROCESS


                else:
                    # Schutz vor IndexError: Mindestens 2 Bytes nötig für Längen-Byte
                    if len(clear_receive_buffer) < 2:
                        print("Index Error - this case should not be entered!")
                    else:
                        laengen_byte = clear_receive_buffer[1]
                        erwartete_gesamtlaenge = laengen_byte + 6

                        if len(clear_receive_buffer) >= erwartete_gesamtlaenge:
                            # Telegramm ist vollständig da! Jetzt final prüfen:

                            if clear_receive_buffer[erwartete_gesamtlaenge - 1] == 0x16:
                                end_byte_ok = True
                                print("Telegram ending sign 0x16 detected")
                            else:
                                end_byte_ok = False


                            geschuetzter_bereich = clear_receive_buffer[4 : 4 + laengen_byte]
                            berechnete_cs = sum(geschuetzter_bereich) & 0xFF
                            empfangene_cs = clear_receive_buffer[erwartete_gesamtlaenge - 2]
                            
                            if end_byte_ok and (berechnete_cs == empfangene_cs):
                                print(f"  [ERFOLG] Gültiges S1-Telegramm von ID {current_id} empfangen!")
                                
                                # Puffer restlos leeren für die RES0-Phase
                                clear_receive_buffer = b""
                                raw_receive_buffer = b""
                                ser_conn.reset_input_buffer()
                                
                                last_send = now
                                state = TlsState.SEND_RES0
                            else:
                                print("  [WARNUNG] Telegramm korrupt (Endzeichen oder CS falsch).")
                                clear_receive_buffer = b""
                                raw_receive_buffer = b""
                                last_send = now
                                ser_conn.reset_input_buffer()
                                if is_scan_mode: 
                                    state = TlsState.RESTART_PROCESS
                                else:
                                    state = TlsState.FINISH_PROCESS


            case TlsState.SEND_RES0:
                if (now - last_send) >= TWP:
                    telegramm = build_ft12_telegram(control_byte=0x40, addr=current_id)
                    print(f"\n  [State: SEND_RES0] Wartezeit Twp erfüllt. Sende RES0 (0x40) an ID {current_id}...")
                    
                    raw_receive_buffer = b""
                    clear_receive_buffer = b""
                    ser_conn.write(telegramm)
                    ser_conn.flush()
                    last_send = now
                    state = TlsState.WAIT_FOR_RR

            case TlsState.WAIT_FOR_RR:
                # Die Reset-Quittung (RR) besteht laut Norm aus exakt 1 Byte (0xE5)
                if len(clear_receive_buffer) >= 1:
                    # Wir prüfen, ob das Zeichen 0xE5 im Puffer liegt
                    if 0xE5 in clear_receive_buffer:
                        print(f"  [State: WAIT_FOR_RR] Einzelzeichen-Quittung (0xE5) von ID {current_id} erfolgreich empfangen!")
                        success = True
                        last_send = now
                        state = TlsState.FINISH_PROCESS
                elif (now - last_send) >= TAP:
                    print(f"  [State: WAIT_FOR_RR] Timeout (Tap={int(TAP*1000)}ms) für Reset-Quittung abgelaufen.")
                    if not is_scan_mode:
                        success = False
                        state = TlsState.FINISH_PROCESS
                    else:
                        if current_id < 199:
                            raw_receive_buffer = b""
                            clear_receive_buffer = b""
                            state = TlsState.RESTART_PROCESS
                        else:
                            success = False
                            state = TlsState.FINISH_PROCESS

            case TlsState.RESTART_PROCESS:
                if current_id < 199:
                    current_id += 1
                    raw_receive_buffer = b""
                    clear_receive_buffer = b""
                    state = TlsState.SEND_RQS
                else:
                    print("  [State: RESTART_PROCESS] Limit von ID 199 erreicht. Kein Sensor gefunden.")
                    success = False
                    state = TlsState.FINISH_PROCESS


            case TlsState.FINISH_PROCESS:
                print(f"\n*** [State: FINISH_PROCESS] Beende State Machine. Ergebnis Success = {success} (Finale ID: {current_id}) ***\n")
                return success

        # KORREKTUR: Exakt 1 Millisekunde Sleep für optimale CPU-Schonung bei 9600 Baud
        time.sleep(0.001)


def main() -> None:
    # Wir testen die zwei gängigsten TLS-Modi (8E1 und 7E1) nacheinander durch
    konfigurationen = [
        {"name": "9600 Baud, 8E1", "bytesize": serial.EIGHTBITS, "parity": serial.PARITY_EVEN},
        {"name": "19200 Baud, 8E1", "bytesize": serial.EIGHTBITS, "parity": serial.PARITY_EVEN},
        # {"name": "9600 Baud, 8O1", "bytesize": serial.EIGHTBITS, "parity": serial.PARITY_ODD},
        # {"name": "9600 Baud, 8N1", "bytesize": serial.EIGHTBITS, "parity": serial.PARITY_NONE},
        # {"name": "9600 Baud, 7E1", "bytesize": serial.SEVENBITS, "parity": serial.PARITY_EVEN},
        # {"name": "9600 Baud, 7O1", "bytesize": serial.SEVENBITS, "parity": serial.PARITY_ODD},
        
    ]
    
    for konfig in konfigurationen:
        print(f"\n==================================================")
        print(f"Teste Sensor-Verbindung mit: {konfig['name']}...")
        print(f"==================================================")
        
        try:
            ser = serial.Serial(
                port=PORT,
                baudrate=9600,
                parity=konfig["parity"],
                bytesize=konfig["bytesize"],
                stopbits=serial.STOPBITS_ONE,
                timeout=2.0
            )
            
            time.sleep(1.0)  # Einschwingzeit für Linux-Kernel & Wandler

            reaktion = run_tls_state_machine(ser_conn=ser, target_addr=0,search_address=True)
            
            ser.close()
            
            if reaktion:
                print(f"\n[Erfolg] Der Sensor hat im Modus {konfig['name']} reagiert!")
                break
            else:
                print(f"\n[Kein Erfolg] Der Sensor hat im Modus {konfig['name']} nicht erfolgreich initialisiert!")
                continue
                
        except serial.SerialException as se:
            print(f"Fehler beim Öffnen von {PORT}: {se}")
            continue
        except Exception as e:
            print(f"Unerwarteter Fehler: {e}")
            continue


if __name__ == "__main__":
    main()
    input("\nDrücke ENTER zum Beenden...")
