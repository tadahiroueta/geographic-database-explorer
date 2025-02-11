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
        post_process = self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH))
        self.assertEqual(type(next(post_process)), events.DatabaseOpenedEvent,
                         "Failed to open database.")

    def test_cannot_open_database(self):
        NON_EXISTENT_DATABASE_FILENAME = "non_existent.db"

        non_existent_database_path = pathlib.Path(NON_EXISTENT_DATABASE_FILENAME)

        post_process = self._engine._handle_open_database(
            events.OpenDatabaseEvent(non_existent_database_path))
        self.assertEqual(type(next(post_process)), events.DatabaseOpenFailedEvent,
                         "Opened non existent database.")

    def test_quit(self):
        post_process = self._engine._handle_quit(events.QuitInitiatedEvent())
        self.assertEqual(type(next(post_process)), events.EndApplicationEvent,
                         "Failed to quit.")

    def test_close_database(self):
        RANDOM_INJECTION = "SELECT * FROM sqlite_master;"

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_close_database(events.CloseDatabaseEvent())

        self.assertEqual(type(next(post_process)), events.DatabaseClosedEvent,
                         "Failed to send event for closing database.")
        with self.assertRaises(sqlite3.ProgrammingError, msg="Failed to actually close database."):
            self._engine._connection.execute(RANDOM_INJECTION)


    def test_search_one_continent_by_code_and_name(self):
        CONTINENT_ID = 1
        CONTINENT_CODE = "AF"
        CONTINENT_NAME = "Africa"

        correct_continent = events.Continent(continent_id=CONTINENT_ID,
                                             continent_code=CONTINENT_CODE, name=CONTINENT_NAME)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_search_continent(
            events.StartContinentSearchEvent(CONTINENT_CODE, CONTINENT_NAME))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to find exactly one continent.")

        first_response = response[0]
        self.assertEqual(type(first_response), events.ContinentSearchResultEvent,
                         "Failed to yield a continent result.")
        self.assertEqual(first_response.continent(), correct_continent,
                         "Failed to find the correct continent.")

    def test_search_one_continent_by_code(self):
        CONTINENT_ID = 1
        CONTINENT_CODE = "AF"
        CONTINENT_NAME = "Africa"

        correct_continent = events.Continent(continent_id=CONTINENT_ID,
                                             continent_code=CONTINENT_CODE, name=CONTINENT_NAME)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_search_continent(
            events.StartContinentSearchEvent(CONTINENT_CODE, ""))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to find exactly one continent.")

        first_response = response[0]
        self.assertEqual(type(first_response), events.ContinentSearchResultEvent,
                         "Failed to yield a continent result.")
        self.assertEqual(first_response.continent(), correct_continent,
                         "Failed to find the correct continent.")

    def test_search_one_continent_by_name(self):
        CONTINENT_ID = 1
        CONTINENT_CODE = "AF"
        CONTINENT_NAME = "Africa"

        correct_continent = events.Continent(continent_id=CONTINENT_ID,
                                             continent_code=CONTINENT_CODE, name=CONTINENT_NAME)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_search_continent(
            events.StartContinentSearchEvent("", CONTINENT_NAME))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to find exactly one continent.")

        first_response = response[0]
        self.assertEqual(type(first_response), events.ContinentSearchResultEvent,
                         "Failed to yield a continent result.")
        self.assertEqual(first_response.continent(), correct_continent,
                         "Failed to find the correct continent.")

    def test_search_two_continents_by_name(self):
        CONTINENT_1_ID = 5
        CONTINENT_1_CODE = "NA"
        CONTINENT_1_NAME = "North America"
        CONTINENT_2_ID = 7
        CONTINENT_2_CODE = "SA"
        CONTINENT_2_NAME = "South America"

        correct_search_result_1 = events.ContinentSearchResultEvent(
            events.Continent(continent_id=CONTINENT_1_ID, continent_code=CONTINENT_1_CODE,
                             name=CONTINENT_1_NAME))

        correct_search_result_2 = events.ContinentSearchResultEvent(
            events.Continent(continent_id=CONTINENT_2_ID,
                                                  continent_code=CONTINENT_2_CODE,
                                                  name=CONTINENT_2_NAME))

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_search_continent(
            events.StartContinentSearchEvent("", "America"))

        response = list(post_process)
        self.assertEqual(len(response), 2, "Failed to find exactly two continents.")
        self.assertIn(correct_search_result_1, response, "Failed to find North America.")
        self.assertIn(correct_search_result_2, response, "Failed to find South America.")

    def test_search_no_continents(self):
        NON_EXISTING_CONTINENT_CODE = "ZZ"

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_search_continent(
            events.StartContinentSearchEvent(NON_EXISTING_CONTINENT_CODE, ""))

        response = list(post_process)
        self.assertEqual(len(response), 0, "Found a non-existent continent.")

if __name__ == '__main__':
    unittest.main()