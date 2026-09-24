$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

if (-not (Test-Path ".venv")) {
    py -3.12 -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
& .\.venv\Scripts\pyside6-qmllint.exe src\niku_calendar\qml\Main.qml
& .\.venv\Scripts\pyinstaller.exe --noconfirm --clean NikuCalendar.spec

Write-Host "Built dist\NikuCalendar.exe"
