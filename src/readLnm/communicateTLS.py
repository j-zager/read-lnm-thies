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
    WAIT_FOR_S1 = auto()
    SEND_RES0 = auto()
    WAIT_FOR_RR = auto()
    RESTART_PROCESS = auto()
    FINISH_PROCESS = auto()


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
    
    # JETZT: Jedes Byte bitweise umdrehen für die TLS-Leitungs-Reihenfolge
    #mirrored_bytes = [reverse_bits(b) for b in normal_telegram]

    # 1. Schritt: Erstelle eine leere Liste, in der wir die gespiegelten Bytes sammeln.
    mirrored_bytes_liste = []

    # 2. Schritt: Starte eine klassische Schleife.
    # Wir gehen nacheinander jedes einzelne Byte aus dem normalen Telegramm durch.
    for b in normal_telegram:
        
        # 3. Schritt: Rufe die Umdreh-Funktion für das EINE aktuelle Byte auf.
        # Das Ergebnis (die umgedrehte Zahl) speichern wir kurz zwischen.
        umgedrehtes_einzel_byte = reverse_bits(b)
        
        # 4. Schritt: Hänge das umgedrehte Byte hinten an unsere Sammel-Liste an.
        mirrored_bytes_liste.append(umgedrehtes_einzel_byte)

    # Am Ende verwandeln wir die Liste wieder in ein echtes Python 'bytes'-Objekt.
    mirrored_bytes = bytes(mirrored_bytes_liste)
    return mirrored_bytes

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

    print(f"\n*** Starte TLS State Machine (Scan-Modus: {is_scan_mode}, Start-Ziel-ID: {target_addr}) ***")

    while True:
        now = time.time()

        # --- ASYNCHRONER EINLESE-TEIL (SCHLEIFENKOPF) ---
        # Liest im 1-ms-Takt ein – exakt abgestimmt auf die Zeichengeschwindigkeit bei 9600 Baud
        if ser_conn.in_waiting > 0:
            bytes_waiting = ser_conn.in_waiting
            new_raw_bytes = ser_conn.read(bytes_waiting)
            raw_receive_buffer += new_raw_bytes
            
            new_clear_bytes = unmirror_response_bytes(new_raw_bytes)
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
                    state = TlsState.WAIT_FOR_S1


            case TlsState.WAIT_FOR_S1:
                s1_komplett = False
                erwartete_gesamtlaenge = 0
                
                # REINIGUNG ÜBER DIE MAIN-SCHLEIFE:
                # Wenn der Puffer Daten enthält, aber nicht mit 0x68 anfängt,
                # werfen wir NUR das erste Byte weg und lassen die Hauptschleife neu durchlaufen.
                if len(clear_receive_buffer) > 0 and clear_receive_buffer[0] != 0x68:
                    # print(f"  [Parser] Verwerfe 1 Byte Rauschen: 0x{clear_receive_buffer[0]:02X}")
                    clear_receive_buffer = clear_receive_buffer[1:]
                    # WICHTIG: Den restlichen Code in diesem Durchlauf überspringen,
                    # damit der Puffer im nächsten Schleifendurchlauf neu bewertet wird.
                    continue 

                # Jetzt wissen wir: WENN Bytes im Puffer sind, fängt der Puffer mit 0x68 an.
                # Wir brauchen mindestens 4 Bytes, um den FT1.2-Header zu validieren.
                if len(clear_receive_buffer) >= 4:
                    
                    # FT1.2-Spezifikation: Byte 0 und Byte 3 MÜSSEN 0x68 sein.
                    if clear_receive_buffer[0] == 0x68 and clear_receive_buffer[3] == 0x68:
                        laengen_byte = clear_receive_buffer[1]
                        erwartete_gesamtlaenge = laengen_byte + 6
                        
                        # Warten, bis der gesamte Rahmen (stückchenweise) eingetroffen ist
                        if len(clear_receive_buffer) >= erwartete_gesamtlaenge:
                            
                            # Letztes Byte auf das offizielle TLS-Endezeichen (0x16) prüfen
                            if clear_receive_buffer[erwartete_gesamtlaenge - 1] == 0x16:
                                
                                # Mathematische Prüfsummenvalidierung (Checksum)
                                geschuetzter_bereich = clear_receive_buffer[4 : 4 + laengen_byte]
                                berechnete_cs = sum(geschuetzter_bereich) & 0xFF
                                empfangene_cs = clear_receive_buffer[erwartete_gesamtlaenge - 2]
                                
                                if berechnete_cs == empfangene_cs:
                                    s1_komplett = True
                                else:
                                    print(f"  [WARNUNG] CS-Fehler bei ID {current_id}! Berechnet: {berechnete_cs:02X}, Empfangen: {empfangene_cs:02X}")
                                    # Defekten Rahmen abschneiden, um den Puffer für neue Daten zu befreien
                                    clear_receive_buffer = clear_receive_buffer[erwartete_gesamtlaenge:]
                            else:
                                print(f"  [WARNUNG] Protokoll-Fehler: Endzeichen ist 0x{clear_receive_buffer[erwartete_gesamtlaenge - 1]:02X} statt 0x16. Rahmen verworfen.")
                                clear_receive_buffer = clear_receive_buffer[erwartete_gesamtlaenge:]
                    else:
                        # Fall: Puffer begann mit 0x68, aber Byte Index 3 ist kein 0x68. 
                        # Das war ein Fehltreffer (Rauschen). Wir löschen das erste Byte und suchen weiter.
                        clear_receive_buffer = clear_receive_buffer[1:]

                # --- AUSWERTUNG STATUS ---
                if s1_komplett:
                    print(f"  [State: WAIT_FOR_S1] Gültiges S1-Telegramm von ID {current_id} dynamisch & CS-geprüft erkannt!")
                    print(f"                       Inhalt: {clear_receive_buffer[:erwartete_gesamtlaenge].hex().upper()}")
                    
                    # 1. Erst sauber abschneiden (falls Rauschen direkt anhing)
                    clear_receive_buffer = clear_receive_buffer[erwartete_gesamtlaenge:]
                    raw_receive_buffer = raw_receive_buffer[erwartete_gesamtlaenge:]
                    
                    # 2. Den seriellen Puffer des Linux-Kernels komplett leeren.
                    # Das löscht alle elektrischen Geister-Bytes, die beim Abschalten des Sensors entstanden sind.
                    ser_conn.reset_input_buffer()
                    
                    # 3. Auch die Skript-Puffer jetzt final nullen, da wir wissen, dass keine Daten folgen können.
                    clear_receive_buffer = b""
                    raw_receive_buffer = b""
                    
                    # Timings setzen für die 50ms-Sperre (Twp) vor SEND_RES0
                    last_send = now 
                    state = TlsState.SEND_RES0

                    
                elif (now - last_send) >= TAP:
                    print(f"  [State: WAIT_FOR_S1] Timeout (Tap={int(TAP*1000)}ms) für ID {current_id} abgelaufen.")
                    
                    # Puffer komplett für die nächste ID nullen
                    clear_receive_buffer = b""
                    raw_receive_buffer = b""
                    
                    if not is_scan_mode:
                        success = False
                        state = TlsState.FINISH_PROCESS
                    else:
                        last_send = now 
                        state = TlsState.RESTART_PROCESS


            # case TlsState.WAIT_FOR_S1:
                
            #     # S1-Statusantwort ist laut FT1.2 ein variabler Rahmen mit einer Länge von 2.
            #     # Gesamtlänge auf der Leitung: Länge (2) + 6 Bytes Hülle = 8 Bytes.
            #     if len(clear_receive_buffer) >= 8:
            #         # Gegenprüfung, ob der Rahmen korrekt formatiert ist (Start=0x68, Ende=0x16)
            #         if clear_receive_buffer[0] == 0x68 and clear_receive_buffer[7] == 0x16:
            #             print(f"  [State: WAIT_FOR_S1] Gültiges 8-Byte S1-Telegramm von ID {current_id} erkannt!")
            #             print(f"                       Inhalt: {clear_receive_buffer.hex().upper()}")
                        
            #             # TIMING 6.1.2: Setzt die 50 ms Twp-Sperre ab dem exakten Erhalts-Zeitpunkt!
            #             last_send = now 
            #             state = TlsState.SEND_RES0
            #     elif (now - last_send) >= TAP:
            #         print(f"  [State: WAIT_FOR_S1] Timeout (Tap={int(TAP*1000)}ms) für ID {current_id} abgelaufen.")
            #         if not is_scan_mode:
            #             success = False
            #             state = TlsState.FINISH_PROCESS
            #         else:
            #             state = TlsState.RESTART_PROCESS

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

            reaktion = run_tls_state_machine(ser_conn=ser, target_addr=1,search_address=True)
            
            ser.close()
            
            if reaktion:
                print(f"\n[Erfolg] Der Sensor hat im Modus {konfig['name']} reagiert!")
                break
            else:
                print(f"\n[Kein Erfolg] Der Sensor hat im Modus {konfig['name']} nicht erfolgreich initialisiert!")
                break
                
        except serial.SerialException as se:
            print(f"Fehler beim Öffnen von {PORT}: {se}")
            continue
        except Exception as e:
            print(f"Unerwarteter Fehler: {e}")
            continue


if __name__ == "__main__":
    main()
    input("\nDrücke ENTER zum Beenden...")
