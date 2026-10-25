import re
import webbrowser
import os
import sys
import subprocess
import platform
import psutil
import gc
from datetime import datetime
from typing import Optional
from urllib.parse import quote_plus


APP_MAP = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "edge": "msedge.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "terminal": "cmd.exe",
    "command prompt": "cmd.exe",
    "task manager": "taskmgr.exe",
    "settings": "ms-settings:",
    "control panel": "control.exe",
}

WEBSITE_ALIASES = {
    "amazon", "facebook", "github", "gmail", "google", "instagram",
    "linkedin", "reddit", "wikipedia", "x", "youtube",
}


class IntentParser:
    def __init__(self):
        self.commands = {
            "open_website": {
                "patterns": [
                    r"open\s+(.+)",
                    r"go\s+to\s+(.+)",
                    r"visit\s+(.+)",
                    r"navigate\s+to\s+(.+)",
                ]
            },
            "search": {
                "patterns": [
                    r"search\s+(?:for\s+)?(.+)",
                    r"look\s+up\s+(.+)",
                    r"google\s+(.+)",
                ]
            },
            "open_app": {
                "patterns": [
                    r"open\s+(?:the\s+)?(.+)",
                    r"launch\s+(.+)",
                    r"start\s+(.+)",
                ]
            },
            "close_app": {
                "patterns": [
                    r"close\s+(?:the\s+)?(.+)",
                    r"exit\s+(.+)",
                    r"quit\s+(.+)",
                ]
            },
            "file_operations": {
                "patterns": [
                    r"create\s+(?:a\s+)?(?:new\s+)?(.+)",
                    r"make\s+(?:a\s+)?(?:new\s+)?(.+)",
                    r"new\s+(.+)",
                ]
            },
            "system_info": {
                "patterns": [r"(?:what\s+is\s+)?the\s+(time|date)"]
            },
            "greeting": {
                "patterns": [r"^(hello|hi|hey|greetings)"]
            },
            "battery_status": {
                "patterns": [r"battery|power|charging|charge"]
            },
            "storage_info": {
                "patterns": [r"storage|disk|space|drive"]
            },
            "memory_info": {
                "patterns": [r"memory|ram|cache"]
            },
            "climate_map": {
                "patterns": [r"temperature|climate|weather"]
            },
            "shutdown": {
                "patterns": [r"shutdown|shut\s+down|power\s+off"]
            },
            "restart": {
                "patterns": [r"restart|reboot"]
            },
        }

    def parse(self, text: str) -> Optional[dict]:
        if not text:
            return None
        text = text.strip().strip(" .!?\t")
        if re.fullmatch(r"(?:hello|hi|hey|greetings)(?: there)?", text, re.IGNORECASE):
            return {"intent": "greeting", "params": {}}

        # Resolve specific actions before the broad "open ..." command.
        priority = [
            ("shutdown", r"\b(?:shutdown|shut\s+down|power\s+off)\b"),
            ("restart", r"\b(?:restart|reboot)\b"),
            ("close_app", r"\b(?:close|exit|quit)\s+(?:the\s+)?(.+)"),
            ("search", r"\b(?:search\s+(?:for\s+)?|look\s+up\s+|google\s+)(.+)"),
            ("file_operations", r"\b(?:create|make|new)\s+(?:a\s+)?(?:new\s+)?(.+)"),
            ("system_info", r"\b(?:what\s+is\s+)?(?:the\s+)?(time|date)\b|\bwhat\s+time\s+is\s+it\b"),
            ("battery_status", r"\b(?:battery|power|charging|charge)\b"),
            ("storage_info", r"\b(?:storage|disk|space|drive)\b"),
            ("memory_info", r"\b(?:memory|ram|cache)\b"),
            ("climate_map", r"\b(?:temperature|climate|weather)\b"),
        ]
        for intent, pattern in priority:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                query = match.group(1).strip() if match.lastindex and match.group(1) else ""
                params = {"query": query}
                if intent == "file_operations":
                    params["operation"] = "create"
                return {"intent": intent, "params": params}

        # "open notepad" is an app command, while "open youtube" or a URL
        # is a website command.
        match = re.search(r"\b(open|go\s+to|visit|navigate\s+to)\s+(.+)", text, re.IGNORECASE)
        if match:
            action, query = match.group(1).lower(), match.group(2).strip().rstrip(".!?")
            query = re.sub(r"^(?:the|a)\s+", "", query, flags=re.IGNORECASE)
            query = re.sub(r"\s+please$", "", query, flags=re.IGNORECASE)
            normalized = query.lower()
            is_app = normalized in APP_MAP
            if action == "open" and is_app:
                return {"intent": "open_app", "params": {"query": query}}
            if re.search(r"\b(?:file|folder|directory)\b", normalized) and action == "open":
                return {"intent": "file_operations", "params": {"query": query}}
            return {"intent": "open_website", "params": {"query": query}}

        match = re.search(r"\b(?:launch|start|run)\s+(?:the\s+)?(.+)", text, re.IGNORECASE)
        if match:
            return {"intent": "open_app", "params": {"query": match.group(1).strip()}}

        for intent_name, intent_data in self.commands.items():
            if intent_name in {
                "open_website", "open_app", "close_app", "file_operations",
                "search", "greeting", "shutdown", "restart", "battery_status",
                "storage_info", "memory_info", "climate_map",
            }:
                continue
            for pattern in intent_data["patterns"]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return {
                        "intent": intent_name,
                        "params": {
                            "query": match.group(1).strip() if match.lastindex else ""
                        },
                    }
        return None


class SystemExecutor:
    def __init__(self, tts):
        self.tts = tts
        self.os_type = platform.system()

    def execute(self, intent_data: dict):
        if not intent_data:
            self.tts.speak("I didn't quite catch that. Can you repeat?")
            return
        intent = intent_data["intent"]
        params = intent_data["params"]
        handlers = {
            "open_website": self._open_website,
            "search": self._search,
            "open_app": self._open_app,
            "close_app": self._close_app,
            "file_operations": self._file_operations,
            "system_info": self._system_info,
            "greeting": self._greeting,
            "battery_status": self._battery_status,
            "storage_info": self._storage_info,
            "memory_info": self._memory_info,
            "climate_map": self._climate_map,
            "shutdown": self._shutdown,
            "restart": self._restart,
        }
        handler = handlers.get(intent)
        if handler:
            handler(params)
        else:
            self.tts.speak("I'm not sure how to do that yet.")

    def _open_website(self, params):
        query = params.get("query", "")
        if not query:
            self.tts.speak("Which website would you like me to open?")
            return
        query = query.replace(" ", ".")
        if not query.startswith(("http://", "https://")):
            query = f"https://{query}"
        self.tts.speak(f"Opening {query}")
        webbrowser.open(query)

    def _search(self, params):
        query = params.get("query", "")
        if not query:
            self.tts.speak("What would you like me to search for?")
            return
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        self.tts.speak(f"Searching for {query}")
        webbrowser.open(url)

    def _open_app(self, params):
        app_name = params.get("query", "").lower()
        if not app_name:
            self.tts.speak("Which application should I open?")
            return
        self.tts.speak(f"Opening {app_name}")
        app_map = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "file explorer": "explorer.exe",
            "explorer": "explorer.exe",
            "terminal": "cmd.exe",
            "command prompt": "cmd.exe",
            "task manager": "taskmgr.exe",
            "settings": "ms-settings:",
            "control panel": "control.exe",
        }
        cmd = app_map.get(app_name, app_name)
        try:
            if self.os_type == "Windows":
                os.startfile(cmd)
            elif self.os_type == "Darwin":
                subprocess.Popen(["open", "-a", app_name])
            else:
                subprocess.Popen(cmd, shell=True)
        except Exception as e:
            self.tts.speak(f"Sorry, I couldn't open {app_name}. Error: {str(e)}")

    def _close_app(self, params):
        app_name = params.get("query", "").lower()
        if not app_name:
            self.tts.speak("Which application should I close?")
            return
        self.tts.speak(f"Closing {app_name}")
        try:
            if self.os_type == "Windows":
                subprocess.Popen(f"taskkill /IM {app_name}.exe /F", shell=True)
            else:
                subprocess.Popen(["killall", app_name])
        except Exception as e:
            self.tts.speak(f"Sorry, I couldn't close {app_name}.")

    def _file_operations(self, params):
        query = params.get("query", "")
        if params.get("operation") == "create":
            self.tts.speak(
                "Creating files and folders is not implemented yet. "
                "I can open File Explorer for you."
            )
            return
        if "file" in query or "folder" in query or "directory" in query:
            self.tts.speak("Opening file explorer.")
            if self.os_type == "Windows":
                os.startfile(".")
            elif self.os_type == "Darwin":
                subprocess.Popen(["open", "."])
            else:
                subprocess.Popen(["xdg-open", "."])
        else:
            self.tts.speak("I can help with opening files or folders. Please specify.")

    def _system_info(self, params):
        query = params.get("query", "").lower()
        if "time" in query:
            current_time = datetime.now().strftime("%I:%M %p")
            self.tts.speak(f"The current time is {current_time}")
        elif "date" in query:
            current_date = datetime.now().strftime("%B %d, %Y")
            self.tts.speak(f"Today's date is {current_date}")
        else:
            current_time = datetime.now().strftime("%I:%M %p")
            current_date = datetime.now().strftime("%B %d, %Y")
            self.tts.speak(f"Today is {current_date} and the time is {current_time}")

    def _battery_status(self, params):
        try:
            battery = psutil.sensors_battery()
            if battery:
                percent = battery.percent
                plugged = battery.power_plugged
                status = "charging" if plugged else "on battery"
                self.tts.speak(
                    f"Battery is at {percent} percent and currently {status}."
                )
            else:
                self.tts.speak("No battery detected on this system.")
        except Exception as e:
            self.tts.speak("Sorry, I'm unable to retrieve battery information.")

    def _storage_info(self, params):
        try:
            root_path = os.path.abspath(os.sep)
            disk = psutil.disk_usage(root_path)
            total_gb = disk.total / (1024 ** 3)
            used_gb = disk.used / (1024 ** 3)
            free_gb = disk.free / (1024 ** 3)
            self.tts.speak(
                f"Storage readout: {total_gb:.1f} gigabytes total, "
                f"{used_gb:.1f} used, {free_gb:.1f} gigabytes free."
            )
        except Exception as e:
            self.tts.speak("Sorry, I'm unable to retrieve disk information.")

    def _memory_info(self, params):
        try:
            mem_before = psutil.virtual_memory().percent
            gc.collect()
            mem_after = psutil.virtual_memory().percent
            self.tts.speak(
                f"Memory saturation was {mem_before} percent. "
                f"After optimization, current usage is {mem_after} percent."
            )
        except Exception as e:
            self.tts.speak("Sorry, I'm unable to retrieve memory diagnostics.")

    def _climate_map(self, params):
        try:
            self.tts.speak("Launching live climate and weather map.")
            webbrowser.open("https://www.google.com/search?q=weather+map+near+me")
        except Exception as e:
            self.tts.speak("Sorry, I couldn't open the weather map.")

    def _greeting(self, params):
        self.tts.speak("Hello! I'm SMILES, your desktop assistant. How can I help you?")

    def _shutdown(self, params):
        self.tts.speak("Shutting down the system. Goodbye!")
        if self.os_type == "Windows":
            os.system('shutdown /s /t 60 /c "SMILES Assistant initiated shutdown"')
        else:
            os.system('shutdown -h +1 "SMILES Assistant initiated shutdown"')

    def _restart(self, params):
        self.tts.speak("Restarting the system. Goodbye!")
        if self.os_type == "Windows":
            os.system('shutdown /r /t 60 /c "SMILES Assistant initiated restart"')
        else:
            os.system('shutdown -r +1 "SMILES Assistant initiated restart"')
