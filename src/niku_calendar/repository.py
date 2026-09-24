from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .core import normalize_activity


class CalendarRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS activities (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reminders (
                occurrence_id TEXT PRIMARY KEY,
                sent_at TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def list_activities(self) -> list[dict[str, Any]]:
        rows = self.connection.execute("SELECT payload FROM activities ORDER BY updated_at, id").fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def save_activity(self, raw: dict[str, Any]) -> dict[str, Any]:
        identifier = str(raw.get("id") or uuid.uuid4())
        activity = normalize_activity(raw, identifier=identifier)
        self.connection.execute(
            """INSERT INTO activities(id, payload, updated_at) VALUES (?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at""",
            (identifier, json.dumps(activity, ensure_ascii=True), datetime.now().isoformat()),
        )
        self.connection.commit()
        return activity

    def delete_activity(self, identifier: str) -> bool:
        cursor = self.connection.execute("DELETE FROM activities WHERE id = ?", (identifier,))
        self.connection.commit()
        return cursor.rowcount > 0

    def replace_activities(self, activities: list[dict[str, Any]]) -> None:
        with self.connection:
            self.connection.execute("DELETE FROM activities")
            timestamp = datetime.now().isoformat()
            self.connection.executemany(
                "INSERT INTO activities(id, payload, updated_at) VALUES (?, ?, ?)",
                [
                    (activity["id"], json.dumps(normalize_activity(activity), ensure_ascii=True), timestamp)
                    for activity in activities
                ],
            )

    def setting(self, key: str, default: str = "") -> str:
        row = self.connection.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        self.connection.execute(
            """INSERT INTO settings(key, value) VALUES (?, ?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
            (key, value),
        )
        self.connection.commit()

    def reminder_was_sent(self, occurrence_id: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM reminders WHERE occurrence_id = ?", (occurrence_id,)
        ).fetchone()
        return row is not None

    def mark_reminder_sent(self, occurrence_id: str) -> None:
        self.connection.execute(
            "INSERT OR IGNORE INTO reminders(occurrence_id, sent_at) VALUES (?, ?)",
            (occurrence_id, datetime.now().isoformat()),
        )
        self.connection.commit()

    def prune_reminders(self, now: datetime | None = None) -> None:
        cutoff = (now or datetime.now()) - timedelta(days=45)
        self.connection.execute("DELETE FROM reminders WHERE sent_at < ?", (cutoff.isoformat(),))
        self.connection.commit()
