import unittest
from datetime import date, datetime

from niku_calendar.core import (
    ValidationError,
    build_events,
    normalize_activity,
    occurrence_dates,
    parse_csv_text,
)


def activity(**changes):
    raw = {
        "id": "standup",
        "title": "Daily stand-up",
        "startDate": "2026-09-21",
        "startTime": "09:00",
        "endTime": "09:30",
        "location": "Room 2",
        "notes": "",
        "links": [],
        "recurrence": {"type": "none", "interval": 1, "weekdays": [], "until": ""},
    }
    raw.update(changes)
    return normalize_activity(raw)


class CoreTests(unittest.TestCase):
    def test_normalizes_required_fields(self):
        item = activity(title="  Planning  ", location="  Desk  ")
        self.assertEqual(item["title"], "Planning")
        self.assertEqual(item["location"], "Desk")

    def test_rejects_invalid_fields(self):
        for field, value in (("title", ""), ("startDate", "09/21/2026"), ("startTime", "9am")):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                activity(**{field: value})

    def test_daily_recurrence_obeys_interval_and_until(self):
        item = activity(
            recurrence={"type": "daily", "interval": 2, "weekdays": [], "until": "2026-09-27"}
        )
        self.assertEqual(
            list(occurrence_dates(item, date(2026, 9, 20), date(2026, 9, 30))),
            [date(2026, 9, 21), date(2026, 9, 23), date(2026, 9, 25), date(2026, 9, 27)],
        )

    def test_weekly_recurrence_uses_selected_weekdays(self):
        item = activity(
            recurrence={"type": "weekly", "interval": 1, "weekdays": [0, 2, 4], "until": ""}
        )
        self.assertEqual(
            list(occurrence_dates(item, date(2026, 9, 21), date(2026, 9, 27))),
            [date(2026, 9, 21), date(2026, 9, 23), date(2026, 9, 25)],
        )

    def test_monthly_recurrence_clamps_without_permanent_drift(self):
        item = activity(
            startDate="2024-01-31",
            recurrence={"type": "monthly", "interval": 1, "weekdays": [], "until": ""},
        )
        self.assertEqual(
            list(occurrence_dates(item, date(2024, 1, 1), date(2024, 4, 30))),
            [date(2024, 1, 31), date(2024, 2, 29), date(2024, 3, 31), date(2024, 4, 30)],
        )

    def test_yearly_leap_day_returns_to_leap_day(self):
        item = activity(
            startDate="2024-02-29",
            recurrence={"type": "yearly", "interval": 1, "weekdays": [], "until": ""},
        )
        occurrences = list(occurrence_dates(item, date(2024, 1, 1), date(2028, 12, 31)))
        self.assertEqual(occurrences[-1], date(2028, 2, 29))

    def test_indefinite_recurrence_continues_after_ten_years(self):
        item = activity(
            startDate="2000-01-01",
            recurrence={"type": "yearly", "interval": 1, "weekdays": [], "until": ""},
        )
        self.assertEqual(
            list(occurrence_dates(item, date(2026, 1, 1), date(2026, 12, 31))),
            [date(2026, 1, 1)],
        )

    def test_fortnight_is_anchored_to_calendar_week(self):
        item = activity(
            startDate="2026-09-23",
            recurrence={"type": "weekly", "interval": 2, "weekdays": [0], "until": ""},
        )
        self.assertEqual(
            list(occurrence_dates(item, date(2026, 9, 23), date(2026, 10, 12))),
            [date(2026, 10, 5)],
        )

    def test_recurrence_near_maximum_date_does_not_overflow(self):
        item = activity(
            startDate="9999-01-01",
            recurrence={"type": "yearly", "interval": 1, "weekdays": [], "until": ""},
        )
        self.assertEqual(
            list(occurrence_dates(item, date(9999, 1, 1), date.max)),
            [date(9999, 1, 1)],
        )

    def test_event_states_and_overnight_end(self):
        overnight = activity(startTime="23:30", endTime="00:30")
        events = build_events(
            [overnight],
            date(2026, 9, 21),
            date(2026, 9, 21),
            now=datetime(2026, 9, 21, 23, 45),
        )
        self.assertEqual(events[0]["state"], "active")
        self.assertEqual(events[0]["endsAt"], "2026-09-22T00:30")

    def test_csv_accepts_english_headers_and_semicolon(self):
        result = parse_csv_text(
            "title;date;start;end;location;recurrence;weekdays\n"
            "Planning;2026-09-21;09:00;10:00;Desk;weekly;0,2\n"
        )
        self.assertEqual(result.activities[0]["title"], "Planning")
        self.assertEqual(result.activities[0]["recurrence"]["weekdays"], [0, 2])

    def test_csv_accepts_spanish_headers_and_skips_bad_rows(self):
        result = parse_csv_text(
            "titulo,fecha,inicio,fin\n"
            "Valida,2026-09-21,09:00,10:00\n"
            "Rota,not-a-date,11:00,12:00\n"
        )
        self.assertEqual(len(result.activities), 1)
        self.assertEqual(len(result.warnings), 1)
        self.assertTrue(result.warnings[0].startswith("Line 3:"))

    def test_csv_requires_a_complete_header(self):
        with self.assertRaisesRegex(ValidationError, "missing"):
            parse_csv_text("title,date,start\nMeeting,2026-09-21,09:00\n")

    def test_csv_duplicate_identifiers_are_reported(self):
        result = parse_csv_text(
            "id,title,date,start,end\n"
            "same,First,2026-09-21,09:00,10:00\n"
            "same,Second,2026-09-22,09:00,10:00\n"
        )
        self.assertEqual([item["title"] for item in result.activities], ["First"])
        self.assertIn("duplicate", result.warnings[0])


if __name__ == "__main__":
    unittest.main()
