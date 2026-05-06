import asyncio
import argparse
from readLnm.commands import cli_menu 
from readLnm.processManager import do_single_message
from readLnm.processManager import portSelection
from readLnm.myLogger import get_logger, setup_logger

logger = get_logger(__name__)




from enum import Enum, auto

class State(Enum):
    INIT = auto()
    REQUEST_MESSAGE = auto()
    SEND_MESSAGE = auto()
    CHECK_MESSAGE = auto()
    RECEIVE_MESSAGE = auto()
    IDLE = auto()
    EXIT = auto()


async def run_fsm():
    fsm_state = State.INIT
    msg = None
    response = None

    while True:
        match fsm_state:

            # -------------------------
            case State.INIT:
                print("STATE: INIT")
                port =portSelection()
                fsm_state = State.REQUEST_MESSAGE
                continue

            # -------------------------
            case State.REQUEST_MESSAGE:
                print("STATE: REQUEST_MESSAGE")
                msg = cli_menu()

                if msg is None:
                    continue

                action = confirm_message(msg)

                if action == "send":
                    fsm_state = State.SEND_MESSAGE
                elif action == "retry":
                    fsm_state = State.REQUEST_MESSAGE
                elif action == "quit":
                    fsm_state = State.EXIT
                continue

            # -------------------------
            case State.SEND_MESSAGE:
                print("STATE: SEND_MESSAGE")
                response = await do_single_message(msg,port)
                fsm_state = State.CHECK_MESSAGE
                print("")
                continue

            # -------------------------
            case State.CHECK_MESSAGE:
                print("STATE: CHECK_MESSAGE")
                if response:
                    fsm_state = State.RECEIVE_MESSAGE
                else:
                    #print("Keine Antwort erhalten.")
                    fsm_state = State.IDLE
                continue

            # -------------------------
            case State.RECEIVE_MESSAGE:
                print("STATE: RECEIVE_MESSAGE")
                print("Antwort:", response)
                fsm_state = State.IDLE
                continue

            # -------------------------
            case State.IDLE:
                print("STATE: IDLE")
                again = input("Neue Nachricht senden? (J/N): ").strip().lower()
                if again == "j" or again == "":
                    msg = None
                    response = None
                    fsm_state = State.REQUEST_MESSAGE
                else:
                    fsm_state = State.EXIT
                continue

            # -------------------------
            case State.EXIT:
                print("STATE: EXIT")
                print("Alle Ressourcen wurden freigegeben. Programm endet.")
                break



def confirm_message(msg: bytes) -> str:
    """
    Fragt den Benutzer, ob das Telegramm gesendet, neu eingegeben
    oder das Programm beendet werden soll.

    Rückgabe:
        "send"  → Nachricht senden
        "retry" → neue Eingabe
        "quit"  → Programm beenden
    """

    print(f"\nTelegramm: {msg}")

    while True:
        choice = input("\nSenden (J), neu eingeben (N), beenden (Q): ").strip().lower()

        if choice == "j" or choice =="":
            return "send"
        elif choice == "n":
            return "retry"
        elif choice == "q":
            return "quit"
        else:
            print("❌ Ungültige Eingabe! Bitte J, N oder Q eingeben.")



def parse_args():
    parser = argparse.ArgumentParser(description="Kommunikation mit LNM Thies")
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Aktiviere Debug-Logging"
    )
    return parser.parse_args()

def communicate():
    args = parse_args()

    # Debug-Mode abhängig vom Parameter
    debug_mode = args.debug

    # Logger JETZT konfigurieren
    setup_logger(
        debug_mode=debug_mode,
        logfile_name="climate_LNM_Thies.log"
    )
    logger.debug("Debug Modus aktiviert")
    logger.info("Starte LNM Kommunikation")
    asyncio.run(run_fsm())

if __name__ == "__main__":
    communicate()