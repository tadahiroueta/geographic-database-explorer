import pathlib
import sqlite3
import unittest
from contextlib import contextmanager

import p2app.engine as engine
import p2app.events as events


DATABASE_FILENAME = "../airport.db"
DATABASE_PATH = pathlib.Path(DATABASE_FILENAME)


class MyTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._engine = engine.Engine()

    def test_open_database(self):
        post_process = self._engine.process_event(events.OpenDatabaseEvent(DATABASE_PATH))
        self.assertEqual(type(next(post_process)), events.DatabaseOpenedEvent,
                         "Failed to open database.")

    def test_cannot_open_database(self):
        NON_EXISTENT_DATABASE_FILENAME = "non_existent.db"

        non_existent_database_path = pathlib.Path(NON_EXISTENT_DATABASE_FILENAME)

        post_process = self._engine.process_event(
            events.OpenDatabaseEvent(non_existent_database_path))
        self.assertEqual(type(next(post_process)), events.DatabaseOpenFailedEvent,
                         "Opened non existent database.")

    def test_quit(self):
        post_process = self._engine.process_event(events.QuitInitiatedEvent())
        self.assertEqual(type(next(post_process)), events.EndApplicationEvent,
                         "Failed to quit.")

    def test_close_database(self):
        RANDOM_INJECTION = "SELECT * FROM sqlite_master;"

        for _ in self._engine.process_event(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine.process_event(events.CloseDatabaseEvent())

        self.assertEqual(type(next(post_process)), events.DatabaseClosedEvent,
                         "Failed to send event for closing database.")
        with self.assertRaises(sqlite3.ProgrammingError, msg="Failed to actually close database."):
            self._engine._connection.execute(RANDOM_INJECTION)

if __name__ == '__main__':
    unittest.main()