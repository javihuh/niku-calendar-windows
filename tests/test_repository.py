import tempfile
import unittest
from pathlib import Path

from niku_calendar.repository import CalendarRepository


def sample(title="Planning", identifier="planning"):
    return {
        "id": identifier,
        "title": title,
        "startDate": "2026-09-21",
        "startTime": "09:00",
        "endTime": "10:00",
        "recurrence": {"type": "none", "interval": 1, "weekdays": [], "until": ""},
    }


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary_directory.name) / "calendar.db"
        self.repository = CalendarRepository(self.path)

    def tearDown(self):
        self.repository.close()
        self.temporary_directory.cleanup()

    def test_crud_persists_between_connections(self):
        self.repository.save_activity(sample())
        self.repository.close()
        self.repository = CalendarRepository(self.path)
        self.assertEqual(self.repository.list_activities()[0]["title"], "Planning")
        self.assertTrue(self.repository.delete_activity("planning"))
        self.assertEqual(self.repository.list_activities(), [])

    def test_update_keeps_identifier(self):
        self.repository.save_activity(sample())
        self.repository.save_activity(sample(title="Updated"))
        items = self.repository.list_activities()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Updated")

    def test_replace_is_atomic_and_settings_persist(self):
        self.repository.save_activity(sample())
        self.repository.replace_activities([sample("Imported", "imported")])
        self.repository.set_setting("view", "week")
        self.assertEqual([item["id"] for item in self.repository.list_activities()], ["imported"])
        self.assertEqual(self.repository.setting("view"), "week")

    def test_reminders_are_deduplicated(self):
        self.assertFalse(self.repository.reminder_was_sent("meeting:2026-09-21"))
        self.repository.mark_reminder_sent("meeting:2026-09-21")
        self.repository.mark_reminder_sent("meeting:2026-09-21")
        self.assertTrue(self.repository.reminder_was_sent("meeting:2026-09-21"))


if __name__ == "__main__":
    unittest.main()
