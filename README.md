# Niku Calendar for Windows

Niku Calendar is a small cat-themed calendar that lives in the Windows system tray. Click the cat icon to open a compact Day or Week panel, manage recurring activities, import CSV schedules, and receive a notification ten minutes before an event.

## Features

- Day and Week views with upcoming, active, and occurred states
- One-time, daily, weekly, monthly, and yearly activities
- Local create, edit, and delete workflow
- CSV preview with merge and replace modes
- Native Windows tray icon and reminder notifications
- Optional launch at Windows sign-in
- English and Spanish interface text
- Local SQLite storage with no account or network service

## Install on Windows

1. Open the repository's **Releases** page.
2. Download `NikuCalendar.exe` from the latest release.
3. Move it to a permanent folder, such as `%LOCALAPPDATA%\Programs\NikuCalendar`.
4. Run `NikuCalendar.exe`. If Windows SmartScreen appears, select **More info** and then **Run anyway**. Local unsigned builds trigger this warning.
5. Find the cat icon in the system tray. Windows may place it in the hidden-icons menu.
6. Open **Settings** inside Niku Calendar to enable **Run when Windows starts** if desired.

Niku Calendar is portable. To uninstall it, quit from the tray menu and delete the executable. To also remove calendar data, delete `%LOCALAPPDATA%\JaviHuh\Niku Calendar`.

## Run from source

Python 3.12 or newer is required.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
niku-calendar
```

The application starts in the system tray. Right-click the cat icon to open the panel, add an activity, or quit.

## Build the executable

Run this on Windows PowerShell:

```powershell
.\scripts\build-windows.ps1
```

The standalone executable is written to `dist\NikuCalendar.exe`. Windows may display a SmartScreen warning for unsigned local builds. Code signing can be added later without changing the application.

## CSV format

Required columns are `title`, `startDate`, `startTime`, and `endTime`. Dates use `YYYY-MM-DD`; times use `HH:MM` in 24-hour format.

Optional columns:

| Column | Values |
| --- | --- |
| `location` | Free text |
| `notes` | Free text |
| `recurrence` | `none`, `daily`, `weekly`, `monthly`, `yearly` |
| `interval` | Positive integer, defaults to `1` |
| `weekdays` | Comma-separated numbers, Monday `0` through Sunday `6` |
| `until` | Optional final date in `YYYY-MM-DD` format |

Comma, semicolon, and tab delimiters are detected automatically. Common Spanish header names are accepted. See `examples/schedule.csv`.

Merge uses a stable identifier derived from title, date, and times, so importing the same rows updates them instead of adding duplicates. Replace removes existing activities only after the preview is confirmed.

## Data and privacy

Data is stored in `%LOCALAPPDATA%\JaviHuh\Niku Calendar\niku-calendar.db`. Niku Calendar does not transmit calendar data. Removing the database resets the application.

## Development

Core scheduling and persistence tests do not require Qt:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

The final tray behavior, native notifications, startup registry entry, and packaged executable must be tested on Windows.
