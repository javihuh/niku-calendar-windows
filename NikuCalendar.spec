from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

project = Path(SPECPATH)
source = project / "src" / "niku_calendar"

a = Analysis(
    [str(project / "launcher.py")],
    pathex=[str(project / "src")],
    binaries=[],
    datas=[
        (str(source / "qml"), "niku_calendar/qml"),
        (str(source / "assets"), "niku_calendar/assets"),
    ],
    hiddenimports=collect_submodules("PySide6.QtQml")
    + [
        "PySide6.QtNetwork",
        "PySide6.QtQuick",
        "PySide6.QtQuickControls2",
        "PySide6.QtSvg",
        "niku_calendar.controller",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="NikuCalendar",
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
)
