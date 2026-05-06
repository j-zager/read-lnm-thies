import logging
from logging import FileHandler, StreamHandler
from pathlib import Path

DEBUG_MODE = False

def setup_logger(debug_mode: bool, logfile_name: str | None = None):
    """
    Konfiguriert das zentrale Logging für das gesamte Projekt.
    debug_mode = True  → DEBUG-Level
    debug_mode = False → INFO-Level
    logfile_name = Name der Logdatei (z. B. 'app.log')
    """

    global DEBUG_MODE
    DEBUG_MODE = debug_mode

    level = logging.INFO 
    if debug_mode: 
        level = logging.DEBUG

        # Format abhängig vom Debug-Mode
    if debug_mode:
        # Modulname anzeigen
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    else:
        # KEIN Modulname
        fmt = "%(asctime)s [%(levelname)s] %(message)s"


    formatter = logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")

    # Root-Logger holen
    root = logging.getLogger()
    root.setLevel(level)

    # Doppelte Handler verhindern
    if root.hasHandlers():
        root.handlers.clear()

    # --- Konsolen-Handler ---
    console_handler = StreamHandler()
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    # --- Datei-Handler ---
    if logfile_name:
        # Projekt-Root bestimmen: 3 Ebenen hoch
        # myLogger.py → projektspezifischername → src → projekt-root
        project_root = Path(__file__).resolve().parents[2]

        logfile_path = project_root / logfile_name

        # Datei anlegen, falls sie nicht existiert
        logfile_path.touch(exist_ok=True)

        file_handler = FileHandler(logfile_path, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)


def get_logger(name: str):
    """
    Gibt einen Logger zurück, der in Modulen verwendet wird.
    """
    return logging.getLogger(name)
