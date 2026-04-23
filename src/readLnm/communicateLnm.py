import asyncio
from generic_utils.io.loggerConfig import getLogger
from readLnm.commands import cli_menu #COMMANDS, input_device_id, input_command, input_value, build_message
from readLnm.serialRS485 import do_single_message
from readLnm.handleVirtualPorts import init_virtual_port_selection

logger = getLogger("ThiesLNM comm log")

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
                virtualPort = init_virtual_port_selection()
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
                response = await do_single_message(msg,virtualPort)
                fsm_state = State.CHECK_MESSAGE
                continue

            # -------------------------
            case State.CHECK_MESSAGE:
                print("STATE: CHECK_MESSAGE")
                if response:
                    fsm_state = State.RECEIVE_MESSAGE
                else:
                    print("Keine Antwort erhalten.")
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
                if again == "j":
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

        if choice == "j":
            return "send"
        elif choice == "n":
            return "retry"
        elif choice == "q":
            return "quit"
        else:
            print("❌ Ungültige Eingabe! Bitte J, N oder Q eingeben.")



def communicate():
    logger.info("startLNM com")
    asyncio.run(run_fsm())

if __name__ == "__main__":
    communicate()