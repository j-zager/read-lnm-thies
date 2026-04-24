# COMMANDS = {
#     "KY": {"desc": "Command mode (0=user, 1=config)", "set": True,  "range": (0, 1)},
#     "BR": {"desc": "Baudrate (5 = 9600Bd 8N1)",        "set": True,  "range": (0, 99999)},
#     "BD": {"desc": "Duplex (0=Full, 1=Half)",          "set": True,  "range": (0, 1)},
#     "ID": {"desc": "Device Address",                   "set": True,  "range": (0, 99)},
#     "RS": {"desc": "Reset Sensor (1)",                 "set": True,  "range": (1, 1)},
#     "SV": {"desc": "Software Version",                 "set": False},
#     "SB": {"desc": "Bootloader Version",               "set": False},
#     "SN": {"desc": "Serial Number",                    "set": False},
#     "TM": {"desc": "Telegram Mode (3..10)",            "set": True,  "range": (3, 10)},
#     "TR": {"desc": "Request Telegram (4..7)",          "set": True,  "range": (4, 7)},
#     "TO": {"desc": "Time interval telegram 10 (1..10)", "set": True, "range": (1, 10)},
#     "ZH": {"desc": "Set Hour (0..23)",                 "set": True,  "range": (0, 23)},
#     "ZM": {"desc": "Set Minute (0..59)",               "set": True,  "range": (0, 59)},
#     "ZS": {"desc": "Set Second (0..59)",               "set": True,  "range": (0, 59)},
#     "ZD": {"desc": "Set Day (1..31)",                  "set": True,  "range": (1, 31)},
#     "ZN": {"desc": "Set Month (1..12)",                "set": True,  "range": (1, 12)},
#     "ZY": {"desc": "Set Year (0..99)",                 "set": True,  "range": (0, 99)},
#     "ZT": {"desc": "Get Sensor Date + Time",           "set": False},
#     "DX": {"desc": "Self Diagnostic",                  "set": False},
#     "FM": {"desc": "Error Count",                      "set": False},
#     "RF": {"desc": "Reset Error Count (1)",            "set": True,  "range": (1, 1)},
#     "AT": {"desc": "Temp calibration (0..106)",        "set": True,  "range": (0, 106)},
#     "AV": {"desc": "Amount Adjustment (80..120%)",     "set": True,  "range": (80, 120)},
#     "AU": {"desc": "Measuring Area",                   "set": False},
#     "RA": {"desc": "Reset Amount (1)",                 "set": True,  "range": (1, 1)},
#     "PT": {"desc": "Time Duration Amount",             "set": False},
#     "D1": {"desc": "Digital Output 1",                 "set": True,  "range": (0, 1)},
#     "D2": {"desc": "Digital Output 2",                 "set": True,  "range": (0, 1)},
#     "DA": {"desc": "Auxiliary Measuring Channel",      "set": True,  "range": (0, 99999)},
#     "HK": {"desc": "Heating head (0/1)",               "set": True,  "range": (0, 1)},
#     "HB": {"desc": "Heating holder (0/1)",             "set": True,  "range": (0, 1)},
#     "HG": {"desc": "Heating housing (0/1)",            "set": True,  "range": (0, 1)},
#     "YD": {"desc": "Distribution data (3-4 chars)",    "set": True,  "range": (0, 9999)},
#     "AC": {"desc": "Mittelungstrigger",                "set": False},
#     "AG": {"desc": "Abgleich Groeßenmessung",          "set": False},
#     "AP": {"desc": "Analoge Versorgung",               "set": False},
#     "AX": {"desc": "Abgleich 100 Ohm Referenz",        "set": False},
#     "AY": {"desc": "Abgleich 127 Ohm Referenz",        "set": False},
#     "AZ": {"desc": "Zeitkalibration",                  "set": False},
#     "OR": {"desc": "Ausgaberate",                      "set": False},
#     "TC": {"desc": "Interner Trigger",                 "set": False},
#     "TV": {"desc": "Interner Triggerwert",             "set": False},
# }


COMMANDS = {
    "KY": {"desc": "Command mode (0=user, 1=config)",  "set": True,  "range": (0, 1), "rx_len": 10},
    "BR": {"desc": "Baudrate (5 = 9600Bd 8N1)",        "set": True,  "range": (0, 99999), "rx_len": 10},
    "BD": {"desc": "Duplex (0=Full, 1=Half)",          "set": True,  "range": (0, 1), "rx_len": 10},
    "ID": {"desc": "Device Address",                   "set": True,  "range": (0, 99), "rx_len": 10},
    "RS": {"desc": "Reset Sensor (1)",                 "set": True,  "range": (1, 1), "rx_len": 10},
    "SV": {"desc": "Software Version",                 "set": False, "rx_len": 10},
    "SB": {"desc": "Bootloader Version",               "set": False, "rx_len": 10},
    "SN": {"desc": "Serial Number",                    "set": False, "rx_len": 10},
    "TM": {"desc": "Telegram Mode (3..10)",            "set": True,  "range": (3, 10), "rx_len": 10},
    "TR": {"desc": "Request Telegram (4..7)",          "set": True,  "range": (4, 7), "rx_len": 10},
    "TO": {"desc": "Time interval telegram 10 (1..10)","set": True, "range": (1, 10), "rx_len": 10},
    "ZH": {"desc": "Set Hour (0..23)",                 "set": True,  "range": (0, 23), "rx_len": 10},
    "ZM": {"desc": "Set Minute (0..59)",               "set": True,  "range": (0, 59), "rx_len": 10},
    "ZS": {"desc": "Set Second (0..59)",               "set": True,  "range": (0, 59), "rx_len": 10},
    "ZD": {"desc": "Set Day (1..31)",                  "set": True,  "range": (1, 31), "rx_len": 10},
    "ZN": {"desc": "Set Month (1..12)",                "set": True,  "range": (1, 12), "rx_len": 10},
    "ZY": {"desc": "Set Year (0..99)",                 "set": True,  "range": (0, 99), "rx_len": 10},
    "ZT": {"desc": "Get Sensor Date + Time",           "set": False, "rx_len": 17},
    "DX": {"desc": "Self Diagnostic",                  "set": False, "rx_len": 10},
    "FM": {"desc": "Error Count",                      "set": False, "rx_len": 10},
    "RF": {"desc": "Reset Error Count (1)",            "set": True,  "range": (1, 1), "rx_len": 10},
    "AT": {"desc": "Temp calibration (0..106)",        "set": True,  "range": (0, 106), "rx_len": 10},
    "AV": {"desc": "Amount Adjustment (80..120%)",     "set": True,  "range": (80, 120), "rx_len": 10},
    "AU": {"desc": "Measuring Area",                   "set": False, "rx_len": 10},
    "RA": {"desc": "Reset Amount (1)",                 "set": True,  "range": (1, 1), "rx_len": 10},
    "PT": {"desc": "Time Duration Amount",             "set": False, "rx_len": 10},
    "D1": {"desc": "Digital Output 1",                 "set": True,  "range": (0, 1), "rx_len": 10},
    "D2": {"desc": "Digital Output 2",                 "set": True,  "range": (0, 1), "rx_len": 10},
    "DA": {"desc": "Auxiliary Measuring Channel",      "set": True,  "range": (0, 99999), "rx_len": 20},
    "DD": {"desc": "Diagnostic Data",                  "set": True,  "range": (0, 99999), "rx_len": 58},
    "DX": {"desc": "Error/Warning Data",               "set": True,  "range": (0, 99999), "rx_len": 31},
    "HK": {"desc": "Heating head (0/1)",               "set": True,  "range": (0, 1), "rx_len": 10},
    "HB": {"desc": "Heating holder (0/1)",             "set": True,  "range": (0, 1), "rx_len": 10},
    "HG": {"desc": "Heating housing (0/1)",            "set": True,  "range": (0, 1), "rx_len": 10},
    "YD": {"desc": "Distribution data (3-4 chars)",    "set": True,  "range": (0, 9999), "rx_len": 10},
    "AC": {"desc": "Mittelungstrigger",                "set": False, "rx_len": 10},
    "AG": {"desc": "Abgleich Groeßenmessung",          "set": False, "rx_len": 10},
    "AP": {"desc": "Analoge Versorgung",               "set": False, "rx_len": 10},
    "AX": {"desc": "Abgleich 100 Ohm Referenz",        "set": False, "rx_len": 10},
    "AY": {"desc": "Abgleich 127 Ohm Referenz",        "set": False, "rx_len": 10},
    "AZ": {"desc": "Zeitkalibration",                  "set": False, "rx_len": 10},
    "OR": {"desc": "Ausgaberate",                      "set": False, "rx_len": 10},
    "TC": {"desc": "Interner Trigger",                 "set": False, "rx_len": 10},
    "TV": {"desc": "Interner Triggerwert",             "set": False, "rx_len": 10},
}


def is_set_command(msg: bytes) -> bool:
    # 5 Zeichen = READ
    # 10 Zeichen = SET
    length = len(msg)

    if length == 5:
        return False  # READ → Antwort erwartet

    if length == 10:
        return True   # SET → keine Antwort

    # Alles andere ist ungültig
    raise ValueError(f"Ungültige Telegrammlänge: {length}")


def input_command()-> str:
    while True:
        cmd = input("Befehl eingeben: ").strip().upper()
        if cmd in COMMANDS:
            return cmd
        print("❌ Ungültiger Befehl! Bitte erneut eingeben.")

def input_device_id()-> int:
    while True:
        dev = input("Geräteadresse (00-99, Default 00): ").strip()
        if dev == "":
            return 0
        if dev.isdigit() and 0 <= int(dev) <= 99:
            return int(dev)
        print("❌ Ungültige Geräteadresse!")

def input_value(cmd)-> int:
    info = COMMANDS[cmd]
    low, high = info["range"]

    while True:
        val = input(f"Parameterwert ({low}..{high}): ").strip()
        if val.isdigit() and low <= int(val) <= high:
            return int(val)
        print("❌ Ungültiger Wert!")


def build_message(command: str, device_id: int = 0, value: int | None = None) -> bytes:
    """
    Baut ein Telegramm nach dem Format:
    <id><BB><ppppp><CR>
    """

    id_str = f"{device_id:02d}"        # 2-stellig, führende Nullen
    cmd_str = command.upper()          # Befehlscode

    if value is None:
        msg = f"{id_str}{cmd_str}\r"
    else:
        msg = f"{id_str}{cmd_str}{value:05d}\r"  # 5-stellig, führende Nullen

    return msg.encode("ascii")


def cli_menu():
    print("=== LNM Thies RS232 CLI Menü ===")
    print("1) Lesen")
    print("2) Setzen")
    print("================================")

    mode = input("Modus wählen (1/2): ").strip()
    while mode not in ("1", "2"):
        mode = input("❌ Ungültig! Modus wählen (1/2): ").strip()

    dev_id = input_device_id()

    print("\nVerfügbare Befehle:")
    for cmd, info in COMMANDS.items():
        print(f" {cmd} = {info['desc']}")
    print()

    cmd = input_command()

    # Prüfen, ob der Befehl Setzen erlaubt
    if mode == "2":
        if not COMMANDS[cmd]["set"]:
            print(f"❌ Befehl {cmd} unterstützt kein Setzen!")
            return None

        val = input_value(cmd)
        msg = build_message(cmd, dev_id, val)
    else:
        msg = build_message(cmd, dev_id, None)

    print("\nErzeugtes Telegramm:", msg)
    return msg




def get_rx_len_from_msg(msg: bytes) -> int:
    """
    Extrahiert den Command-Code aus einem Telegramm wie b"00SV\r"
    und gibt die erwartete rx_len zurück.
    Standard: 10
    Fehlerfall: 0
    """
    try:
        cmd = msg[2:4].decode("ascii")
    except Exception:
        return 0  # ungültiges Telegramm

    entry = COMMANDS.get(cmd)
    if entry is None:
        return 0  # unbekannter Command

    return entry.get("rx_len", 0)
