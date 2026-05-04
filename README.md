# LNM Thies RS485 Communication Tool

This project provides a command‑line interface (CLI) and communication framework for interacting with Thies LNM sensors over RS485.
It supports building valid telegrams, reading and writing device parameters, and handling communication through an internal finite state machine (FSM). 
The tool can handle regulary traffic messages and can handle specific data formats like ZT.

The tool can be executed in three different ways:

    via the installed script entry point

    via python -m readLnm

    via python -m readLnm.communicateLnm

## 🚀 Features

    Interactive CLI menu for building telegrams

    Automatic validation of commands and parameter ranges

    Asynchronous RS485 communication

    Finite state machine (FSM) for structured communication flow

  


## 📦 Installation

Install the package locally:

pip install .

Or install in development mode:

pip install -e .

Python 3.10 or newer is required (due to match-case).
▶️ How to Run the Tool

After installation, you can start the tool in three different ways:
### 1️⃣ Using the script entry point

Defined in your pyproject.toml:

[project.scripts]
comLnmThies = "readLnm.communicateLnm:communicate"

Run it directly:

comLnm

### 2️⃣ Running the main package

This executes readLnm/__main__.py:

python -m readLnm

### 3️⃣ Running the communication module directly

This calls the communicate() function inside the module:

python -m readLnm.communicateLnm



## 🧭 CLI Workflow

The CLI guides the user through:

    Selecting mode

        Read

        Write

    Entering device ID

        Automatically formatted to 2 digits (00–99)

    Selecting a command

        All commands are listed dynamically from the internal command dictionary

    Entering a parameter value (if required)

        Automatic validation

        Range checking based on command definition

    Confirming the telegram

        Send

        Re-enter

        Quit

## 🔧 Telegram Format

The tool automatically generates valid telegrams according to the Thies protocol:

<id><BB><ppppp><CR>

Where:

    id: device address (00–99)

    BB: command code (e.g., SV, BR, TM)

    ppppp: optional 5‑digit parameter (zero‑padded)

    CR: carriage return (\r)

Examples:

00SV\r
03SB\r
00BR00005\r

## 🧠 Finite State Machine (FSM)

The communication flow is controlled by a small FSM with the following states:
State	Description
INIT	Setup and initialization
REQUEST_MESSAGE	Build telegram via CLI
SEND_MESSAGE	Send telegram over RS232
CHECK_MESSAGE	Validate response
RECEIVE_MESSAGE	Process received data
IDLE	Wait for next action
EXIT	Clean shutdown of ports and resources


## 📚 Command Dictionary

All supported commands are defined in a structured dictionary:


COMMANDS = {
    "KY": {"desc": "Command mode (0=user, 1=config)",  "set": True,  "range": (0, 1), "rx_len": 10},
    "BR": {"desc": "Baudrate (5 = 9600Bd 8N1)",        "set": True,  "range": (0, 99999), "rx_len": 10},

        ...
}

This enables:

    automatic menu generation

    input validation

    parameter range checking

