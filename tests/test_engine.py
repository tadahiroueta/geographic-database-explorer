import pathlib
import sqlite3
import unittest
from contextlib import contextmanager

import p2app.engine as engine
import p2app.events as events


class MyTestCase(unittest.TestCase):

    @classmethod
    def setUpDatabase(cls):
        """
        Creates a database, or if already existing, clears it.
        """
        DATABASE_FILENAME = "test_database.db"

        cls._database_path = pathlib.Path(DATABASE_FILENAME)
        cls._connection = sqlite3.connect(DATABASE_FILENAME)
        cls._cursor = cls._connection.cursor()

        # foreign key constraint configuration
        cls._cursor.execute("PRAGMA foreign_keys = ON;")

        # dropping all tables
        cls._cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = cls._cursor.fetchall()
        for table in existing_tables:
            name = table[0]
            cls._cursor.execute(f"DROP TABLE { name };")

        cls._connection.commit()

    @classmethod
    def setUpClass(cls):
        cls.setUpDatabase()
        cls._engine = engine.Engine()

    @classmethod
    def tearDownClass(cls):
        cls._cursor.close()
        cls._connection.close()

    @contextmanager
    def create_table(self, table_name: str, injection: str):
        """
        Creates a table temporarily.

        Args:
            table_name (str): Name of the table to create.
            injection (str): SQL injection to create a table.
        """
        self._cursor.execute(injection)
        self._connection.commit()

        yield

        self._cursor.execute(f"DROP TABLE { table_name };")
        self._connection.commit()

    def test_open_database(self):
        post_process = self._engine.process_event(events.OpenDatabaseEvent(self._database_path))
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

        for _ in self._engine.process_event(events.OpenDatabaseEvent(self._database_path)):
            pass
        post_process = self._engine.process_event(events.CloseDatabaseEvent())

        self.assertEqual(type(next(post_process)), events.DatabaseClosedEvent,
                         "Failed to send event for closing database.")
        with self.assertRaises(sqlite3.ProgrammingError, msg="Failed to actually close database."):
            self._engine._connection.execute(RANDOM_INJECTION)

if __name__ == '__main__':
    unittest.main()