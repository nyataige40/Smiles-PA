"""Small, allowlisted tools the language model can use on this computer."""

import os
import platform
import subprocess
import webbrowser
from datetime import datetime
from urllib.parse import quote_plus, urlparse

import psutil


APP_COMMANDS = {
    "notepad": {
        "Windows": ["notepad.exe"],
        "Darwin": ["open", "-a", "TextEdit"],
        "Linux": ["gedit"],
    },
    "calculator": {
        "Windows": ["calc.exe"],
        "Darwin": ["open", "-a", "Calculator"],
        "Linux": ["gnome-calculator"],
    },
    "paint": {
        "Windows": ["mspaint.exe"],
        "Darwin": ["open", "-a", "Preview"],
        "Linux": ["pinta"],
    },
    "chrome": {
        "Windows": ["chrome.exe"],
        "Darwin": ["open", "-a", "Google Chrome"],
        "Linux": ["google-chrome"],
    },
    "firefox": {
        "Windows": ["firefox.exe"],
        "Darwin": ["open", "-a", "Firefox"],
        "Linux": ["firefox"],
    },
    "edge": {
        "Windows": ["msedge.exe"],
        "Darwin": ["open", "-a", "Microsoft Edge"],
        "Linux": ["microsoft-edge"],
    },
    "file explorer": {
        "Windows": ["explorer.exe"],
        "Darwin": ["open", "-a", "Finder"],
        "Linux": ["xdg-open", os.path.expanduser("~")],
    },
    "terminal": {
        "Windows": ["cmd.exe"],
        "Darwin": ["open", "-a", "Terminal"],
        "Linux": ["x-terminal-emulator"],
    },
    "task manager": {
        "Windows": ["taskmgr.exe"],
        "Darwin": ["open", "-a", "Activity Monitor"],
        "Linux": ["gnome-system-monitor"],
    },
    "settings": {
        "Windows": ["ms-settings:"],
        "Darwin": ["open", "-a", "System Settings"],
        "Linux": ["gnome-control-center"],
    },
    "control panel": {"Windows": ["control.exe"]},
}

APP_ALIASES = {
    "calc": "calculator",
    "file manager": "file explorer",
    "finder": "file explorer",
    "text editor": "notepad",
}

WEBSITE_ALIASES = {
    "amazon": "https://www.amazon.com",
    "facebook": "https://www.facebook.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "instagram": "https://www.instagram.com",
    "linkedin": "https://www.linkedin.com",
    "reddit": "https://www.reddit.com",
    "wikipedia": "https://www.wikipedia.org",
    "youtube": "https://www.youtube.com",
}


def open_application(app_name: str) -> dict:
    """Open an installed application from the supported app list.

    Args:
        app_name: Name of a supported app, such as Notepad or Calculator.
    """
    name = app_name.strip().lower()
    name = APP_ALIASES.get(name, name)
    commands = APP_COMMANDS.get(name)
    if not commands:
        return {
            "ok": False,
            "message": f"'{app_name}' is not in the supported app list.",
            "supported_apps": sorted(APP_COMMANDS),
        }

    command = commands.get(platform.system())
    if not command:
        return {"ok": False, "message": f"'{name}' is not configured for this operating system."}

    try:
        if platform.system() == "Windows":
            os.startfile(command[0])
        else:
            subprocess.Popen(command, shell=False)
        return {"ok": True, "message": f"Opened {name}."}
    except (OSError, ValueError) as exc:
        return {"ok": False, "message": f"Could not open {name}: {exc}"}


def open_website(url: str) -> dict:
    """Open a website in the default browser; only HTTP and HTTPS are allowed.

    Args:
        url: A website URL or a supported site name such as YouTube.
    """
    address = url.strip()
    if not address:
        return {"ok": False, "message": "A website address is required."}
    address = WEBSITE_ALIASES.get(address.lower(), address)
    if not urlparse(address).scheme:
        if "." not in address:
            return {"ok": False, "message": "Please provide a website name or a domain such as example.com."}
        address = f"https://{address}"

    parsed = urlparse(address)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return {"ok": False, "message": "Only valid HTTP or HTTPS website addresses can be opened."}

    try:
        opened = webbrowser.open(address)
        message = f"Opened {address}." if opened else "The browser did not open the website."
        return {"ok": opened, "message": message}
    except Exception as exc:
        return {"ok": False, "message": f"Could not open the website: {exc}"}


def search_web(query: str) -> dict:
    """Open a Google search for the supplied query in the default browser.

    Args:
        query: The words or question to search for.
    """
    query = query.strip()
    if not query:
        return {"ok": False, "message": "A search query is required."}
    try:
        opened = webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")
        message = (
            f"Searching the web for {query}."
            if opened
            else "The browser did not open the search."
        )
        return {"ok": opened, "message": message}
    except Exception as exc:
        return {"ok": False, "message": f"Could not start the search: {exc}"}


def get_current_time() -> dict:
    """Get the computer's current local date and time."""
    now = datetime.now().astimezone()
    return {"date": now.strftime("%A, %B %d, %Y"), "time": now.strftime("%I:%M %p %Z")}


def get_system_status() -> dict:
    """Read current battery, memory, and disk status from the computer."""
    status = {"memory_percent": psutil.virtual_memory().percent}
    try:
        battery = psutil.sensors_battery()
    except (OSError, RuntimeError):
        battery = None
    if battery is None:
        status["battery"] = "not available on this device"
    else:
        status["battery_percent"] = battery.percent
        status["charging"] = battery.power_plugged

    disk = psutil.disk_usage(os.path.abspath(os.sep))
    status["disk_free_gb"] = round(disk.free / (1024 ** 3), 1)
    status["disk_total_gb"] = round(disk.total / (1024 ** 3), 1)
    return status
