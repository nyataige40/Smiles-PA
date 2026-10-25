# SMILES Personal Assistant

SMILES uses Gemini for natural language conversation and function calling. Voice
input remains activated by saying **Jarvis** or **Smiles**. You can also run a
typed chat with `--text`.

## Setup on Windows

From PowerShell in this folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:GEMINI_API_KEY = "your Gemini API key"
python main.py
```

Use `python main.py --text` for typed chat without microphone or speaker access.
Set `GEMINI_MODEL` to override the default model (`gemini-flash-latest`).

SMILES needs an internet connection for both Google speech recognition and the
Gemini API. The API key is read from the environment and is not stored in the
project. Do not commit API keys to source control.

## Available tools

- Open a supported application or an HTTP/HTTPS website.
- Open a Google search in the default browser.
- Read the computer's local time, battery, memory, and disk status.

Conversation history is kept in memory for the current run and is cleared when
SMILES exits. Gemini receives conversation messages to generate replies. SMILES
does not currently send messages, create or delete files, shut down the computer,
or run arbitrary shell commands.
