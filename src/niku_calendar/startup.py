from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "NikuCalendar"


def _command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{Path(sys.executable)}"'
    return f'"{Path(sys.executable)}" -m niku_calendar'


def is_enabled() -> bool:
    if os.name != "nt":
        return False
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run") as key:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
            return value == _command()
    except FileNotFoundError:
        return False


def set_enabled(enabled: bool) -> None:
    if os.name != "nt":
        return
    import winreg

    path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, path) as key:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _command())
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
