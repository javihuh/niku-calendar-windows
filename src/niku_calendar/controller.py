from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QUrl

from .core import ValidationError, build_events, parse_csv_file
from .repository import CalendarRepository
from .startup import is_enabled as startup_is_enabled
from .startup import set_enabled as set_startup_enabled

TEXT = {
    "en": {
        "today": "Today",
        "week": "Week",
        "empty": "No plans yet. A suspicious amount of free time. (=^･ω･^=)",
        "saved": "Activity saved",
        "deleted": "Activity deleted",
        "imported": "Imported {count} activities",
        "reminder": "Starts in 10 minutes",
        "settings": "Settings",
        "add": "+ Add",
        "manage": "Manage",
        "importCsv": "Import CSV",
        "event": "event",
        "events": "events",
        "back": "‹ Back",
        "activities": "Activities",
        "new": "+ New",
        "edit": "Edit",
        "cancel": "‹ Cancel",
        "editActivity": "Edit activity",
        "newActivity": "New activity",
        "title": "Title",
        "date": "Date",
        "start": "Start",
        "end": "End",
        "location": "Location",
        "notes": "Notes",
        "optional": "Optional",
        "repeat": "Repeat",
        "every": "Every",
        "until": "Until",
        "weekdays": "Weekdays (0=Mon … 6=Sun)",
        "linkLabel": "Link label",
        "linkUrl": "Link URL",
        "saveActivity": "Save activity",
        "importPreview": "Import preview",
        "validActivities": "valid activities",
        "skippedRows": "skipped rows",
        "importHelp": "Merge updates matching CSV activities. Replace removes all existing activities first.",
        "replaceAll": "Replace all",
        "mergeImport": "Merge import",
        "calendarName": "Calendar name",
        "language": "Language",
        "runAtStartup": "Run when Windows starts",
        "privacy": "Data stays on this computer in a local SQLite database.",
        "openCalendar": "Open Niku Calendar",
        "quit": "Quit",
        "importSchedule": "Import schedule",
        "encouragements": [
            "One paw at a time. (=｀ω´=)",
            "Your tiny supervisor believes in you. /ᐠ｡ꞈ｡ᐟ\\",
            "A tidy schedule leaves room for naps. ฅ^•ﻌ•^ฅ",
            "You have got this, human. (=^ ◡ ^=)",
        ],
    },
    "es": {
        "today": "Hoy",
        "week": "Semana",
        "empty": "Aun no hay planes. Demasiado tiempo libre sospechoso. (=^･ω･^=)",
        "saved": "Actividad guardada",
        "deleted": "Actividad eliminada",
        "imported": "Se importaron {count} actividades",
        "reminder": "Empieza en 10 minutos",
        "settings": "Ajustes",
        "add": "+ Añadir",
        "manage": "Gestionar",
        "importCsv": "Importar CSV",
        "event": "evento",
        "events": "eventos",
        "back": "‹ Volver",
        "activities": "Actividades",
        "new": "+ Nueva",
        "edit": "Editar",
        "cancel": "‹ Cancelar",
        "editActivity": "Editar actividad",
        "newActivity": "Nueva actividad",
        "title": "Título",
        "date": "Fecha",
        "start": "Inicio",
        "end": "Fin",
        "location": "Ubicación",
        "notes": "Notas",
        "optional": "Opcional",
        "repeat": "Repetir",
        "every": "Cada",
        "until": "Hasta",
        "weekdays": "Días (0=lun … 6=dom)",
        "linkLabel": "Nombre del enlace",
        "linkUrl": "URL del enlace",
        "saveActivity": "Guardar actividad",
        "importPreview": "Vista previa",
        "validActivities": "actividades válidas",
        "skippedRows": "filas omitidas",
        "importHelp": "Combinar actualiza las actividades coincidentes. Reemplazar elimina primero las existentes.",
        "replaceAll": "Reemplazar todo",
        "mergeImport": "Combinar importación",
        "calendarName": "Nombre del calendario",
        "language": "Idioma",
        "runAtStartup": "Iniciar con Windows",
        "privacy": "Los datos permanecen en este equipo, en una base SQLite local.",
        "openCalendar": "Abrir Niku Calendar",
        "quit": "Salir",
        "importSchedule": "Importar horario",
        "encouragements": [
            "Una patita cada vez. (=｀ω´=)",
            "Tu pequeno supervisor confia en ti. /ᐠ｡ꞈ｡ᐟ\\",
            "Una agenda ordenada deja sitio para siestas. ฅ^•ﻌ•^ฅ",
            "Tu puedes, humano. (=^ ◡ ^=)",
        ],
    },
}


class CalendarController(QObject):
    eventsChanged = Signal()
    activitiesChanged = Signal()
    viewChanged = Signal()
    languageChanged = Signal()
    calendarTitleChanged = Signal()
    noticeChanged = Signal()
    editorChanged = Signal()
    importPreviewChanged = Signal()
    runAtStartupChanged = Signal()
    pageRequested = Signal(int)
    reminderDue = Signal(str, str)

    def __init__(self, repository: CalendarRepository) -> None:
        super().__init__()
        self.repository = repository
        self._events: list[dict[str, Any]] = []
        self._activities: list[dict[str, Any]] = []
        self._view = repository.setting("view", "day")
        self._language = repository.setting("language", "en")
        self._calendar_title = repository.setting("calendarTitle", "Niku Calendar")
        self._notice = ""
        self._editor: dict[str, Any] = {}
        self._import_preview: dict[str, Any] = {}
        self.refresh()

    @Property("QVariantList", notify=eventsChanged)
    def events(self) -> list[dict[str, Any]]:
        return self._events

    @Property("QVariantList", notify=activitiesChanged)
    def activities(self) -> list[dict[str, Any]]:
        return self._activities

    @Property(str, notify=viewChanged)
    def view(self) -> str:
        return self._view

    @Property(str, notify=languageChanged)
    def language(self) -> str:
        return self._language

    @Property(str, notify=calendarTitleChanged)
    def calendarTitle(self) -> str:
        return self._calendar_title

    @Property(str, notify=noticeChanged)
    def notice(self) -> str:
        return self._notice

    @Property("QVariantMap", notify=editorChanged)
    def editor(self) -> dict[str, Any]:
        return self._editor

    @Property("QVariantMap", notify=importPreviewChanged)
    def importPreview(self) -> dict[str, Any]:
        return self._import_preview

    @Property(bool, notify=runAtStartupChanged)
    def runAtStartup(self) -> bool:
        return startup_is_enabled()

    @Property(str, constant=True)
    def todayIso(self) -> str:
        return date.today().isoformat()

    @Property(str, notify=languageChanged)
    def encouragement(self) -> str:
        choices = TEXT[self._language]["encouragements"]
        return choices[date.today().toordinal() % len(choices)]

    @Slot(str, result=str)
    def text(self, key: str) -> str:
        value = TEXT[self._language].get(key, key)
        return value if isinstance(value, str) else key

    @Slot()
    def refresh(self) -> None:
        self._activities = self.repository.list_activities()
        today = date.today()
        if self._view == "week":
            first = today - timedelta(days=today.weekday())
            last = first + timedelta(days=6)
        else:
            first = last = today
        visible_start = datetime.combine(first, datetime.min.time())
        visible_end = datetime.combine(last + timedelta(days=1), datetime.min.time())
        events = build_events(self._activities, first - timedelta(days=1), last)
        self._events = [
            event
            for event in events
            if datetime.fromisoformat(event["endsAt"]) > visible_start
            and datetime.fromisoformat(event["startsAt"]) < visible_end
        ]
        self.activitiesChanged.emit()
        self.eventsChanged.emit()

    @Slot(str)
    def setView(self, view: str) -> None:
        if view not in {"day", "week"} or view == self._view:
            return
        self._view = view
        self.repository.set_setting("view", view)
        self.viewChanged.emit()
        self.refresh()

    @Slot(str)
    def setLanguage(self, language: str) -> None:
        if language not in TEXT or language == self._language:
            return
        self._language = language
        self.repository.set_setting("language", language)
        self.languageChanged.emit()

    @Slot(str)
    def setCalendarTitle(self, title: str) -> None:
        title = title.strip()
        if not title:
            return
        self._calendar_title = title
        self.repository.set_setting("calendarTitle", title)
        self.calendarTitleChanged.emit()

    def _set_notice(self, message: str) -> None:
        self._notice = message
        self.noticeChanged.emit()

    @Slot()
    def newActivity(self) -> None:
        self._editor = {
            "id": "",
            "title": "",
            "startDate": date.today().isoformat(),
            "startTime": "09:00",
            "endTime": "10:00",
            "location": "",
            "notes": "",
            "linkLabel": "",
            "linkUrl": "",
            "recurrenceType": "none",
            "interval": "1",
            "weekdays": [],
            "until": "",
        }
        self.editorChanged.emit()
        self.pageRequested.emit(2)

    @Slot(str)
    def editActivity(self, identifier: str) -> None:
        activity = next((item for item in self._activities if item["id"] == identifier), None)
        if not activity:
            return
        recurrence = activity["recurrence"]
        links = activity.get("links", [])
        first_link = links[0] if links else {}
        self._editor = {
            **activity,
            "linkLabel": first_link.get("label", ""),
            "linkUrl": first_link.get("url", ""),
            "recurrenceType": recurrence["type"],
            "interval": str(recurrence["interval"]),
            "weekdays": recurrence["weekdays"],
            "until": recurrence["until"],
        }
        self.editorChanged.emit()
        self.pageRequested.emit(2)

    @Slot("QVariantMap", result=bool)
    def saveActivity(self, raw: dict[str, Any]) -> bool:
        try:
            link_url = str(raw.pop("linkUrl", "")).strip()
            link_label = str(raw.pop("linkLabel", "")).strip()
            raw["links"] = [{"label": link_label or "Link", "url": link_url}] if link_url else []
            raw["recurrence"] = {
                "type": raw.pop("recurrenceType", "none"),
                "interval": raw.pop("interval", 1),
                "weekdays": raw.pop("weekdays", []),
                "until": raw.pop("until", ""),
            }
            self.repository.save_activity(raw)
        except (ValidationError, ValueError) as exc:
            self._set_notice(str(exc))
            return False
        self._set_notice(self.text("saved"))
        self.refresh()
        self.pageRequested.emit(0)
        return True

    @Slot(str)
    def deleteActivity(self, identifier: str) -> None:
        if self.repository.delete_activity(identifier):
            self._set_notice(self.text("deleted"))
            self.refresh()

    @Slot(str)
    def openLink(self, url: str) -> None:
        parsed = QUrl.fromUserInput(url)
        if parsed.isValid() and parsed.scheme() in {"http", "https", "mailto"}:
            QDesktopServices.openUrl(parsed)

    @Slot()
    def chooseCsv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            None, self.text("importSchedule"), "", "CSV files (*.csv)"
        )
        if not path:
            return
        try:
            result = parse_csv_file(path)
        except (OSError, ValidationError) as exc:
            self._set_notice(str(exc))
            return
        self._import_preview = {
            "path": path,
            "name": Path(path).name,
            "count": len(result.activities),
            "warnings": result.warnings,
            "activities": result.activities,
        }
        self.importPreviewChanged.emit()
        self.pageRequested.emit(3)

    @Slot(bool)
    def importCsv(self, replace: bool) -> None:
        activities = self._import_preview.get("activities", [])
        if not activities:
            return
        if replace:
            self.repository.replace_activities(activities)
        else:
            for activity in activities:
                self.repository.save_activity(activity)
        self._set_notice(self.text("imported").format(count=len(activities)))
        self.refresh()
        self.pageRequested.emit(0)

    @Slot(bool)
    def setRunAtStartup(self, enabled: bool) -> None:
        try:
            set_startup_enabled(enabled)
        except OSError as exc:
            self._set_notice(f"Could not update Windows startup: {exc}")
        self.runAtStartupChanged.emit()

    @Slot()
    def checkReminders(self) -> None:
        now = datetime.now()
        reminder_limit = now + timedelta(minutes=10, seconds=30)
        events = build_events(
            self.repository.list_activities(), now.date(), reminder_limit.date(), now=now
        )
        for event in events:
            delta = datetime.fromisoformat(event["startsAt"]) - now
            if timedelta(0) <= delta <= timedelta(minutes=10, seconds=30):
                occurrence_id = event["occurrenceId"]
                if self.repository.reminder_was_sent(occurrence_id):
                    continue
                body = f"{event['startTime']} · {self.text('reminder')}"
                if event["location"]:
                    body += f" · {event['location']}"
                self.reminderDue.emit(event["title"], body)
                self.repository.mark_reminder_sent(occurrence_id)
