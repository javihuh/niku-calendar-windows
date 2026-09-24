from __future__ import annotations

import calendar
import csv
import hashlib
import io
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Iterable

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"
RECURRENCES = {"none", "daily", "weekly", "monthly", "yearly"}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ImportResult:
    activities: list[dict[str, Any]]
    warnings: list[str]


def _text(value: Any) -> str:
    return str(value or "").strip()


def _parse_date(value: Any, field: str) -> date:
    try:
        return datetime.strptime(_text(value), DATE_FORMAT).date()
    except ValueError as exc:
        raise ValidationError(f"{field} must use YYYY-MM-DD") from exc


def _parse_time(value: Any, field: str) -> time:
    try:
        return datetime.strptime(_text(value), TIME_FORMAT).time()
    except ValueError as exc:
        raise ValidationError(f"{field} must use HH:MM") from exc


def _positive_int(value: Any, field: str, default: int = 1) -> int:
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be a number") from exc
    if parsed < 1:
        raise ValidationError(f"{field} must be at least 1")
    return parsed


def normalize_activity(raw: dict[str, Any], *, identifier: str | None = None) -> dict[str, Any]:
    title = _text(raw.get("title"))
    if not title:
        raise ValidationError("title is required")

    start_date = _parse_date(raw.get("startDate"), "startDate")
    start_time = _parse_time(raw.get("startTime"), "startTime")
    end_time = _parse_time(raw.get("endTime"), "endTime")
    recurrence_raw = raw.get("recurrence") or {}
    recurrence_type = _text(recurrence_raw.get("type") or raw.get("recurrenceType") or "none").lower()
    if recurrence_type not in RECURRENCES:
        raise ValidationError(f"unsupported recurrence: {recurrence_type}")

    weekdays_raw = recurrence_raw.get("weekdays", raw.get("weekdays", []))
    if isinstance(weekdays_raw, str):
        weekdays_raw = [part for part in re.split(r"[|,; ]+", weekdays_raw) if part]
    try:
        weekdays = sorted({int(day) for day in weekdays_raw})
    except (TypeError, ValueError) as exc:
        raise ValidationError("weekdays must contain numbers from 0 to 6") from exc
    if any(day < 0 or day > 6 for day in weekdays):
        raise ValidationError("weekdays must contain numbers from 0 to 6")
    if recurrence_type == "weekly" and not weekdays:
        weekdays = [start_date.weekday()]

    until_raw = _text(recurrence_raw.get("until") or raw.get("until"))
    until = _parse_date(until_raw, "until") if until_raw else None
    if until and until < start_date:
        raise ValidationError("until cannot precede startDate")

    links = raw.get("links") or []
    if not isinstance(links, list):
        raise ValidationError("links must be a list")
    normalized_links = []
    for link in links:
        if not isinstance(link, dict) or not _text(link.get("url")):
            continue
        normalized_links.append({"label": _text(link.get("label")) or "Link", "url": _text(link["url"])})

    activity_id = identifier or _text(raw.get("id"))
    if not activity_id:
        source = f"{title}|{start_date.isoformat()}|{start_time:%H:%M}|{end_time:%H:%M}"
        activity_id = hashlib.sha256(source.encode()).hexdigest()[:16]

    return {
        "id": activity_id,
        "title": title,
        "startDate": start_date.isoformat(),
        "startTime": start_time.strftime(TIME_FORMAT),
        "endTime": end_time.strftime(TIME_FORMAT),
        "location": _text(raw.get("location")),
        "notes": _text(raw.get("notes")),
        "links": normalized_links,
        "recurrence": {
            "type": recurrence_type,
            "interval": _positive_int(recurrence_raw.get("interval", raw.get("interval")), "interval"),
            "weekdays": weekdays,
            "until": until.isoformat() if until else "",
        },
    }


def _add_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    year, zero_month = divmod(month_index, 12)
    if year > date.max.year:
        return date.max
    month = zero_month + 1
    return date(year, month, min(value.day, calendar.monthrange(year, month)[1]))


def occurrence_dates(activity: dict[str, Any], start: date, end: date) -> Iterable[date]:
    first = date.fromisoformat(activity["startDate"])
    recurrence = activity["recurrence"]
    kind = recurrence["type"]
    interval = int(recurrence["interval"])
    until = date.fromisoformat(recurrence["until"]) if recurrence["until"] else end
    limit = min(end, until)
    if limit < first or end < start:
        return

    if kind == "none":
        if start <= first <= limit:
            yield first
        return

    if kind == "daily":
        cursor = first
        if start > first:
            steps = (start - first).days // interval
            cursor += timedelta(days=steps * interval)
            while cursor < start:
                cursor += timedelta(days=interval)
        while cursor <= limit:
            yield cursor
            if cursor >= limit:
                break
            cursor += timedelta(days=interval)
        return

    if kind == "weekly":
        weekdays = set(recurrence["weekdays"])
        anchor = first - timedelta(days=first.weekday())
        cursor = max(first, start)
        while cursor <= limit:
            week = (cursor - anchor).days // 7
            if week % interval == 0 and cursor.weekday() in weekdays:
                yield cursor
            if cursor >= limit:
                break
            cursor += timedelta(days=1)
        return

    step_months = interval if kind == "monthly" else interval * 12
    max_months = (date.max.year - first.year) * 12 + date.max.month - first.month
    months_to_start = max(0, (start.year - first.year) * 12 + start.month - first.month)
    index = months_to_start // step_months
    cursor = _add_months(first, index * step_months)
    while cursor < start and cursor < date.max:
        index += 1
        if index * step_months > max_months:
            return
        cursor = _add_months(first, index * step_months)
    while cursor <= limit:
        yield cursor
        if cursor >= limit or cursor == date.max:
            break
        index += 1
        if index * step_months > max_months:
            break
        cursor = _add_months(first, index * step_months)


def build_events(
    activities: Iterable[dict[str, Any]],
    start: date,
    end: date,
    *,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    current = now or datetime.now()
    events: list[dict[str, Any]] = []
    for activity in activities:
        for event_date in occurrence_dates(activity, start, end):
            begins = datetime.combine(event_date, time.fromisoformat(activity["startTime"]))
            finishes = datetime.combine(event_date, time.fromisoformat(activity["endTime"]))
            if finishes <= begins:
                finishes += timedelta(days=1)
            state = "upcoming"
            if current >= finishes:
                state = "occurred"
            elif current >= begins:
                state = "active"
            events.append(
                {
                    **activity,
                    "date": event_date.isoformat(),
                    "dateLabel": event_date.strftime("%a %d %b"),
                    "startsAt": begins.isoformat(timespec="minutes"),
                    "endsAt": finishes.isoformat(timespec="minutes"),
                    "state": state,
                    "occurrenceId": f"{activity['id']}:{event_date.isoformat()}:{activity['startTime']}",
                }
            )
    return sorted(events, key=lambda event: (event["startsAt"], event["title"].casefold()))


HEADER_ALIASES = {
    "title": {"title", "name", "activity", "titulo", "actividad"},
    "startDate": {"startdate", "date", "fecha", "fecha_inicio"},
    "startTime": {"starttime", "start", "inicio", "hora_inicio"},
    "endTime": {"endtime", "end", "fin", "hora_fin"},
    "location": {"location", "place", "ubicacion", "lugar"},
    "notes": {"notes", "description", "notas", "descripcion"},
    "recurrenceType": {"recurrence", "repeat", "recurrencia", "repeticion"},
    "interval": {"interval", "intervalo"},
    "weekdays": {"weekdays", "days", "dias"},
    "until": {"until", "hasta"},
    "id": {"id", "identifier", "identificador"},
}


def _canonical_header(header: str) -> str:
    cleaned = re.sub(r"[^a-z0-9_]+", "", header.strip().casefold())
    for canonical, aliases in HEADER_ALIASES.items():
        if cleaned in aliases:
            return canonical
    return cleaned


def parse_csv_text(content: str) -> ImportResult:
    content = content.lstrip("\ufeff")
    sample = content[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(content), dialect=dialect)
    if not reader.fieldnames:
        raise ValidationError("CSV has no header")
    field_map = {field: _canonical_header(field) for field in reader.fieldnames}
    missing = {"title", "startDate", "startTime", "endTime"} - set(field_map.values())
    if missing:
        raise ValidationError(f"CSV is missing: {', '.join(sorted(missing))}")

    activities: list[dict[str, Any]] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()
    for line_number, row in enumerate(reader, start=2):
        canonical = {field_map[key]: value for key, value in row.items() if key is not None}
        if not any(_text(value) for value in canonical.values()):
            continue
        seed = "|".join(f"{key}={_text(canonical.get(key))}" for key in sorted(canonical))
        identifier = _text(canonical.get("id")) or "csv-" + hashlib.sha256(seed.encode()).hexdigest()[:16]
        if identifier in seen_ids:
            warnings.append(f"Line {line_number}: duplicate activity skipped")
            continue
        try:
            activities.append(normalize_activity(canonical, identifier=identifier))
            seen_ids.add(identifier)
        except ValidationError as exc:
            warnings.append(f"Line {line_number}: {exc}")
    if not activities:
        detail = f" ({warnings[0]})" if warnings else ""
        raise ValidationError(f"CSV contains no valid activities{detail}")
    return ImportResult(activities, warnings)


def parse_csv_file(path: str | Path) -> ImportResult:
    raw = Path(path).read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return parse_csv_text(raw.decode(encoding))
        except UnicodeDecodeError:
            continue
    raise ValidationError("CSV must use UTF-8 or Windows-1252 encoding")
