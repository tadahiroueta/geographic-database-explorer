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
        post_process = self._engine._handle_search_continents(
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
        post_process = self._engine._handle_search_continents(
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
        post_process = self._engine._handle_search_continents(
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

        correct_continent_1 = events.Continent(continent_id=CONTINENT_1_ID,
                                               continent_code=CONTINENT_1_CODE,
                                               name=CONTINENT_1_NAME)
        correct_continent_2 = events.Continent(continent_id=CONTINENT_2_ID,
                                               continent_code=CONTINENT_2_CODE,
                                               name=CONTINENT_2_NAME)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_search_continents(
            events.StartContinentSearchEvent("", "America"))

        response = list(post_process)
        self.assertEqual(len(response), 2, "Failed to find exactly two continents.")
        first_response, second_response = response
        self.assertEqual(first_response.continent(), correct_continent_1,
                         "Failed to find North America.")
        self.assertEqual(second_response.continent(), correct_continent_2,
                      "Failed to find South America.")

    def test_search_no_continents(self):
        NON_EXISTING_CONTINENT_CODE = "ZZ"

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_search_continents(
            events.StartContinentSearchEvent(NON_EXISTING_CONTINENT_CODE, ""))

        response = list(post_process)
        self.assertEqual(len(response), 0, "Found a non-existent continent.")

    def test_load_continents(self):
        CONTINENT_ID = 1
        CONTINENT_CODE = "AF"
        CONTINENT_NAME = "Africa"

        correct_continent = events.Continent(CONTINENT_ID, CONTINENT_CODE, CONTINENT_NAME)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_load_continent(events.LoadContinentEvent(CONTINENT_ID))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to only load continent.")
        only_response = response[0]
        self.assertEqual(type(only_response), events.ContinentLoadedEvent,
                         "Failed to yield a continent loaded event.")
        self.assertEqual(only_response.continent(), correct_continent,
                         "Failed to load the correct continent.")

    def test_save_new_continent(self):
        CONTINENT_ID = 10
        CONTINENT_CODE = "ZZ"
        CONTINENT_NAME = "New Continent"

        new_continent = events.Continent(CONTINENT_ID, CONTINENT_CODE, CONTINENT_NAME)
        delete_continent_injection = f"DELETE FROM continent WHERE continent_id = { CONTINENT_ID };"

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_save_new_continent(
            events.SaveNewContinentEvent(new_continent))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to only save new continent.")
        only_response = response[0]
        self.assertEqual(type(only_response), events.ContinentSavedEvent,
                         "Failed to yield a new continent saved event.")
        self.assertEqual(only_response.continent(), new_continent,
                         "Failed to save the correct continent.")

        cursor = self._engine._connection.execute(delete_continent_injection)
        self._engine._connection.commit()

    def test_do_not_save_new_continent_with_duplicate_id(self):
        CONTINENT_ID = 1
        CONTINENT_CODE = "AF"
        CONTINENT_NAME = "Africa"

        duplicate_continent = events.Continent(CONTINENT_ID, CONTINENT_CODE, CONTINENT_NAME)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_save_new_continent(
            events.SaveNewContinentEvent(duplicate_continent))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to only not save new continent.")
        only_response = response[0]
        self.assertEqual(type(only_response), events.SaveContinentFailedEvent,
                         "Failed to yield a save continent failed event.")

    def test_save_continent(self):
        CONTINENT_ID = 1
        CONTINENT_CODE = "AF"
        CONTINENT_NAME = "Africa"
        MODIFIED_CODE = "FA"
        MODIFIED_NAME = "Modified Africa"

        original_continent = events.Continent(CONTINENT_ID, CONTINENT_CODE, CONTINENT_NAME)
        modified_continent = events.Continent(CONTINENT_ID, MODIFIED_CODE, MODIFIED_NAME)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_save_continent(
            events.SaveContinentEvent(modified_continent))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to only save modified continent.")
        only_response = response[0]
        self.assertEqual(type(only_response), events.ContinentSavedEvent,
                         "Failed to yield a modified continent saved event.")
        self.assertEqual(only_response.continent(), modified_continent,
                         "Failed to save the correct continent.")

        for _ in self._engine._handle_save_continent(events.SaveContinentEvent(original_continent)):
            pass

    def test_do_not_save_continent_with_new_id(self):
        CONTINENT_ID = 10
        CONTINENT_CODE = "ZZ"
        CONTINENT_NAME = "New Continent"

        new_continent = events.Continent(CONTINENT_ID, CONTINENT_CODE, CONTINENT_NAME)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_save_continent(
            events.SaveContinentEvent(new_continent))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to only not save new continent.")
        only_response = response[0]
        self.assertEqual(type(only_response), events.SaveContinentFailedEvent,
                         "Failed to yield a save continent failed event.")

    def test_search_one_country_by_code_and_name(self):
        COUNTRY_ID = 302556
        COUNTRY_CODE = "AO"
        NAME = "Angola"
        CONTINENT_ID = 1
        WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/Angola"
        KEYWORDS = "Angolan airports"

        country = events.Country(COUNTRY_ID, COUNTRY_CODE, NAME, CONTINENT_ID, WIKIPEDIA_LINK,
                                 KEYWORDS)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_search_countries(
            events.StartCountrySearchEvent(COUNTRY_CODE, NAME))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to find exactly one country.")
        first_response = response[0]
        self.assertEqual(type(first_response), events.CountrySearchResultEvent,
                         "Failed to yield a country result.")
        self.assertEqual(first_response.country(), country,
                         "Failed to find the correct country.")

    def test_search_one_country_by_code(self):
        COUNTRY_ID = 302556
        COUNTRY_CODE = "AO"
        NAME = "Angola"
        CONTINENT_ID = 1
        WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/Angola"
        KEYWORDS = "Angolan airports"

        country = events.Country(COUNTRY_ID, COUNTRY_CODE, NAME, CONTINENT_ID, WIKIPEDIA_LINK,
                                 KEYWORDS)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_search_countries(
            events.StartCountrySearchEvent(COUNTRY_CODE, ""))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to find exactly one country.")
        first_response = response[0]
        self.assertEqual(type(first_response), events.CountrySearchResultEvent,
                         "Failed to yield a country result.")
        self.assertEqual(first_response.country(), country,
                         "Failed to find the correct country.")

    def test_search_one_country_by_name(self):
        COUNTRY_ID = 302556
        COUNTRY_CODE = "AO"
        NAME = "Angola"
        CONTINENT_ID = 1
        WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/Angola"
        KEYWORDS = "Angolan airports"

        country = events.Country(COUNTRY_ID, COUNTRY_CODE, NAME, CONTINENT_ID, WIKIPEDIA_LINK,
                                 KEYWORDS)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_search_countries(
            events.StartCountrySearchEvent("", NAME))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to find exactly one country.")
        first_response = response[0]
        self.assertEqual(type(first_response), events.CountrySearchResultEvent,
                         "Failed to yield a country result.")
        self.assertEqual(first_response.country(), country,
                         "Failed to find the correct country.")

    def test_search_two_countries_by_name(self):
        COUNTRY_1_ID = 302642
        COUNTRY_1_CODE = "KP"
        COUNTRY_1_NAME = "North Korea"
        COUNTRY_1_CONTINENT_ID = 3
        COUNTRY_1_WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/North_Korea"
        COUNTRY_1_KEYWORDS = "North Korean airports"
        COUNTRY_2_ID = 302643
        COUNTRY_2_CODE = "KR"
        COUNTRY_2_NAME = "South Korea"
        COUNTRY_2_CONTINENT_ID = 3
        COUNTRY_2_WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/South_Korea"
        COUNTRY_2_KEYWORDS = "한국의 공항"

        country_1 = events.Country(COUNTRY_1_ID, COUNTRY_1_CODE, COUNTRY_1_NAME,
                                   COUNTRY_1_CONTINENT_ID, COUNTRY_1_WIKIPEDIA_LINK,
                                   COUNTRY_1_KEYWORDS)
        country_2 = events.Country(COUNTRY_2_ID, COUNTRY_2_CODE, COUNTRY_2_NAME,
                                   COUNTRY_2_CONTINENT_ID, COUNTRY_2_WIKIPEDIA_LINK,
                                   COUNTRY_2_KEYWORDS)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_search_countries(
            events.StartCountrySearchEvent("", "Korea"))

        response = list(post_process)
        self.assertEqual(len(response), 2, "Failed to find exactly two countries.")
        first_response, second_response = response
        self.assertEqual(first_response.country(), country_1, "Failed to find North Korea.")
        self.assertEqual(second_response.country(), country_2, "Failed to find South Korea.")

    def test_search_no_countries(self):
        NON_EXISTING_COUNTRY_CODE = "YY"

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_search_countries(
            events.StartCountrySearchEvent(NON_EXISTING_COUNTRY_CODE, ""))

        response = list(post_process)
        self.assertEqual(len(response), 0, "Found a non-existent country.")

    def test_load_country(self):
        COUNTRY_ID = 302556
        COUNTRY_CODE = "AO"
        NAME = "Angola"
        CONTINENT_ID = 1
        WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/Angola"
        KEYWORDS = "Angolan airports"

        country = events.Country(COUNTRY_ID, COUNTRY_CODE, NAME, CONTINENT_ID, WIKIPEDIA_LINK,
                                 KEYWORDS)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_load_country(events.LoadCountryEvent(COUNTRY_ID))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to only load country.")
        only_response = response[0]
        self.assertEqual(type(only_response), events.CountryLoadedEvent,
                         "Failed to yield a country loaded event.")
        self.assertEqual(only_response.country(), country, "Failed to load the correct country.")

    def test_save_new_country(self):
        COUNTRY_ID = 999999
        COUNTRY_CODE = "YY"
        NAME = "New Country"
        CONTINENT_ID = 1
        WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/New_Country"
        KEYWORDS = "New Country airports"

        new_country = events.Country(COUNTRY_ID, COUNTRY_CODE, NAME, CONTINENT_ID, WIKIPEDIA_LINK,
                                     KEYWORDS)
        delete_country_injection = f"DELETE FROM country WHERE country_id = { COUNTRY_ID };"

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_save_new_country(
            events.SaveNewCountryEvent(new_country))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to only save new country.")
        only_response = response[0]
        self.assertEqual(type(only_response), events.CountrySavedEvent,
                         "Failed to yield a new country saved event.")
        self.assertEqual(only_response.country(), new_country,
                         "Failed to save the correct country.")

        self._engine._connection.execute(delete_country_injection)
        self._engine._connection.commit()

    def test_do_not_save_new_country_with_duplicate_id(self):
        COUNTRY_ID = 302556
        COUNTRY_CODE = "AO"
        NAME = "Angola"
        CONTINENT_ID = 1
        WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/Angola"
        KEYWORDS = "Angolan airports"

        duplicate_country = events.Country(COUNTRY_ID, COUNTRY_CODE, NAME, CONTINENT_ID,
                                           WIKIPEDIA_LINK, KEYWORDS)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_save_new_country(
            events.SaveNewCountryEvent(duplicate_country))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to only not save new country.")
        only_response = response[0]
        self.assertEqual(type(only_response), events.SaveCountryFailedEvent,
                         "Failed to yield a save country failed event.")

    def test_save_country(self):
        COUNTRY_ID = 302556
        COUNTRY_CODE = "AO"
        NAME = "Angola"
        CONTINENT_ID = 1
        WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/Angola"
        KEYWORDS = "Angolan airports"
        MODIFIED_CODE = "OA"
        MODIFIED_NAME = "Modified Angola"

        original_country = events.Country(COUNTRY_ID, COUNTRY_CODE, NAME, CONTINENT_ID,
                                          WIKIPEDIA_LINK, KEYWORDS)
        modified_country = events.Country(COUNTRY_ID, MODIFIED_CODE, MODIFIED_NAME, CONTINENT_ID,
                                          WIKIPEDIA_LINK, KEYWORDS)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_save_country(
            events.SaveCountryEvent(modified_country))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to only save modified country.")
        only_response = response[0]
        self.assertEqual(type(only_response), events.CountrySavedEvent,
                         "Failed to yield a modified country saved event.")
        self.assertEqual(only_response.country(), modified_country,
                         "Failed to save the correct country.")

        for _ in self._engine._handle_save_country(events.SaveCountryEvent(original_country)):
            pass

    def test_do_not_save_country_with_new_id(self):
        COUNTRY_ID = 999999
        COUNTRY_CODE = "YY"
        NAME = "New Country"
        CONTINENT_ID = 1
        WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/New_Country"
        KEYWORDS = "New Country airports"

        new_country = events.Country(COUNTRY_ID, COUNTRY_CODE, NAME, CONTINENT_ID, WIKIPEDIA_LINK,
                                     KEYWORDS)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_save_country(
            events.SaveCountryEvent(new_country))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to only not save new country.")
        only_response = response[0]
        self.assertEqual(type(only_response), events.SaveCountryFailedEvent,
                         "Failed to yield a save country failed event.")

    def test_search_one_region_by_region_code_local_code_and_name(self):
        REGION_ID = 302811
        REGION_CODE = "AD-02"
        LOCAL_CODE = "02"
        NAME = "Canillo Parish"
        CONTINENT_ID = 4
        COUNTRY_ID = 302672
        WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/Canillo"
        KEYWORDS = "Airports in Canillo Parish"

        region = events.Region(REGION_ID, REGION_CODE, LOCAL_CODE, NAME, CONTINENT_ID, COUNTRY_ID,
                               WIKIPEDIA_LINK, KEYWORDS)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_search_regions(
            events.StartRegionSearchEvent(REGION_CODE, LOCAL_CODE, NAME))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to find exactly one region.")
        first_response = response[0]
        self.assertEqual(type(first_response), events.RegionSearchResultEvent,
                         "Failed to yield a region result.")
        self.assertEqual(first_response.region(), region,
                         "Failed to find the correct region.")

    def test_search_region_by_region_code(self):
        REGION_ID = 302811
        REGION_CODE = "AD-02"
        LOCAL_CODE = "02"
        NAME = "Canillo Parish"
        CONTINENT_ID = 4
        COUNTRY_ID = 302672
        WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/Canillo"
        KEYWORDS = "Airports in Canillo Parish"

        region = events.Region(REGION_ID, REGION_CODE, LOCAL_CODE, NAME, CONTINENT_ID, COUNTRY_ID,
                               WIKIPEDIA_LINK, KEYWORDS)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_search_regions(
            events.StartRegionSearchEvent(REGION_CODE, "", ""))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to find exactly one region.")
        first_response = response[0]
        self.assertEqual(type(first_response), events.RegionSearchResultEvent,
                         "Failed to yield a region result.")
        self.assertEqual(first_response.region(), region,
                         "Failed to find the correct region.")

    def test_search_region_by_local_code(self):
        REGION_ID = 305446
        REGION_CODE = "SI-009"
        LOCAL_CODE = "009"
        NAME = "Brezica"
        CONTINENT_ID = 4
        COUNTRY_ID = 302716
        WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/Brezica"
        KEYWORDS = "Airports in Brezica"

        region = events.Region(REGION_ID, REGION_CODE, LOCAL_CODE, NAME, CONTINENT_ID, COUNTRY_ID,
                               WIKIPEDIA_LINK, KEYWORDS)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_search_regions(
            events.StartRegionSearchEvent("", LOCAL_CODE, ""))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to find exactly one region.")
        first_response = response[0]
        self.assertEqual(type(first_response), events.RegionSearchResultEvent,
                         "Failed to yield a region result.")
        self.assertEqual(first_response.region(), region,
                         "Failed to find the correct region.")

    def test_search_region_by_name(self):
        REGION_ID = 302811
        REGION_CODE = "AD-02"
        LOCAL_CODE = "02"
        NAME = "Canillo Parish"
        CONTINENT_ID = 4
        COUNTRY_ID = 302672
        WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/Canillo"
        KEYWORDS = "Airports in Canillo Parish"

        region = events.Region(REGION_ID, REGION_CODE, LOCAL_CODE, NAME, CONTINENT_ID, COUNTRY_ID,
                               WIKIPEDIA_LINK, KEYWORDS)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_search_regions(
            events.StartRegionSearchEvent("", "", NAME))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to find exactly one region.")
        first_response = response[0]
        self.assertEqual(type(first_response), events.RegionSearchResultEvent,
                         "Failed to yield a region result.")
        self.assertEqual(first_response.region(), region,
                         "Failed to find the correct region.")

    # 303322,CF-AC,AC,Ouham,1,302562,https://en.wikipedia.org/wiki/Ouham,Airports in Ouham
    # 303335,CF-OP,OP,Ouham-Pendé,1,302562,https://en.wikipedia.org/wiki/Ouham-Pend%C3%A9,Airports in Ouham-Pendé

    def test_search_two_regions_by_name(self):
        REGION_1_ID = 303322
        REGION_1_CODE = "CF-AC"
        REGION_1_LOCAL_CODE = "AC"
        REGION_1_NAME = "Ouham"
        REGION_1_CONTINENT_ID = 1
        REGION_1_COUNTRY_ID = 302562
        REGION_1_WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/Ouham"
        REGION_1_KEYWORDS = "Airports in Ouham"
        REGION_2_ID = 303335
        REGION_2_CODE = "CF-OP"
        REGION_2_LOCAL_CODE = "OP"
        REGION_2_NAME = "Ouham-Pendé"
        REGION_2_CONTINENT_ID = 1
        REGION_2_COUNTRY_ID = 302562
        REGION_2_WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/Ouham-Pend%C3%A9"
        REGION_2_KEYWORDS = "Airports in Ouham-Pendé"

        region_1 = events.Region(REGION_1_ID, REGION_1_CODE, REGION_1_LOCAL_CODE, REGION_1_NAME,
                                REGION_1_CONTINENT_ID, REGION_1_COUNTRY_ID, REGION_1_WIKIPEDIA_LINK,
                                REGION_1_KEYWORDS)
        region_2 = events.Region(REGION_2_ID, REGION_2_CODE, REGION_2_LOCAL_CODE, REGION_2_NAME,
                                REGION_2_CONTINENT_ID, REGION_2_COUNTRY_ID, REGION_2_WIKIPEDIA_LINK,
                                REGION_2_KEYWORDS)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_search_regions(
            events.StartRegionSearchEvent("", "", "Ouham"))

        response = list(post_process)
        self.assertEqual(len(response), 2, "Failed to find exactly two regions.")
        first_response, second_response = response
        self.assertEqual(first_response.region(), region_1, "Failed to find Ouham.")
        self.assertEqual(second_response.region(), region_2, "Failed to find Ouham-Pendé.")

    def test_search_no_regions(self):
        NON_EXISTING_REGION_CODE = "YY-99"

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_search_regions(
            events.StartRegionSearchEvent(NON_EXISTING_REGION_CODE, "", ""))

        response = list(post_process)
        self.assertEqual(len(response), 0, "Found a non-existent region.")

    def test_load_region(self):
        REGION_ID = 303322
        REGION_CODE = "CF-AC"
        LOCAL_CODE = "AC"
        NAME = "Ouham"
        CONTINENT_ID = 1
        COUNTRY_ID = 302562
        WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/Ouham"
        KEYWORDS = "Airports in Ouham"

        region = events.Region(REGION_ID, REGION_CODE, LOCAL_CODE, NAME, CONTINENT_ID, COUNTRY_ID,
                               WIKIPEDIA_LINK, KEYWORDS)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_load_region(events.LoadRegionEvent(REGION_ID))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to only load region.")
        only_response = response[0]
        self.assertEqual(type(only_response), events.RegionLoadedEvent,
                         "Failed to yield a region loaded event.")
        self.assertEqual(only_response.region(), region, "Failed to load the correct region.")

    def test_save_new_region(self):
        REGION_ID = 999999
        REGION_CODE = "YY-99"
        LOCAL_CODE = "99"
        NAME = "New Region"
        CONTINENT_ID = 1
        COUNTRY_ID = 302556
        WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/New_Region"
        KEYWORDS = "Airports in New Region"

        new_region = events.Region(REGION_ID, REGION_CODE, LOCAL_CODE, NAME, CONTINENT_ID, COUNTRY_ID,
                                   WIKIPEDIA_LINK, KEYWORDS)
        delete_region_injection = f"DELETE FROM region WHERE region_id = { REGION_ID };"

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_save_new_region(
            events.SaveNewRegionEvent(new_region))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to only save new region.")
        only_response = response[0]
        self.assertEqual(type(only_response), events.RegionSavedEvent,
                         "Failed to yield a new region saved event.")
        self.assertEqual(only_response.region(), new_region, "Failed to save the correct region.")

        self._engine._connection.execute(delete_region_injection)
        self._engine._connection.commit()

    def test_do_not_save_new_region_with_duplicate_id(self):
        REGION_ID = 303322
        REGION_CODE = "CF-AC"
        LOCAL_CODE = "AC"
        NAME = "Ouham"
        CONTINENT_ID = 1
        COUNTRY_ID = 302562
        WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/Ouham"
        KEYWORDS = "Airports in Ouham"

        duplicate_region = events.Region(REGION_ID, REGION_CODE, LOCAL_CODE, NAME, CONTINENT_ID,
                                         COUNTRY_ID, WIKIPEDIA_LINK, KEYWORDS)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_save_new_region(
            events.SaveNewRegionEvent(duplicate_region))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to only not save new region.")
        only_response = response[0]
        self.assertEqual(type(only_response), events.SaveRegionFailedEvent,
                         "Failed to yield a save region failed event.")

    def test_save_region(self):
        REGION_ID = 303322
        REGION_CODE = "CF-AC"
        LOCAL_CODE = "AC"
        NAME = "Ouham"
        CONTINENT_ID = 1
        COUNTRY_ID = 302562
        WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/Ouham"
        KEYWORDS = "Airports in Ouham"
        MODIFIED_CODE = "CF-CA"
        MODIFIED_NAME = "Modified Ouham"

        original_region = events.Region(REGION_ID, REGION_CODE, LOCAL_CODE, NAME, CONTINENT_ID,
                                       COUNTRY_ID, WIKIPEDIA_LINK, KEYWORDS)
        modified_region = events.Region(REGION_ID, MODIFIED_CODE, LOCAL_CODE, MODIFIED_NAME,
                                        CONTINENT_ID, COUNTRY_ID, WIKIPEDIA_LINK, KEYWORDS)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_save_region(
            events.SaveRegionEvent(modified_region))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to only save modified region.")
        only_response = response[0]
        self.assertEqual(type(only_response), events.RegionSavedEvent,
                         "Failed to yield a modified region saved event.")
        self.assertEqual(only_response.region(), modified_region,
                         "Failed to save the correct region.")

        for _ in self._engine._handle_save_region(events.SaveRegionEvent(original_region)):
            pass

    def test_do_not_save_region_with_new_id(self):
        REGION_ID = 999999
        REGION_CODE = "YY-99"
        LOCAL_CODE = "99"
        NAME = "New Region"
        CONTINENT_ID = 1
        COUNTRY_ID = 302556
        WIKIPEDIA_LINK = "https://en.wikipedia.org/wiki/New_Region"
        KEYWORDS = "Airports in New Region"

        new_region = events.Region(REGION_ID, REGION_CODE, LOCAL_CODE, NAME, CONTINENT_ID, COUNTRY_ID,
                                   WIKIPEDIA_LINK, KEYWORDS)

        for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
            pass
        post_process = self._engine._handle_save_region(
            events.SaveRegionEvent(new_region))

        response = list(post_process)
        self.assertEqual(len(response), 1, "Failed to only not save new region.")
        only_response = response[0]
        self.assertEqual(type(only_response), events.SaveRegionFailedEvent,
                         "Failed to yield a save region failed event.")

if __name__ == '__main__':
    unittest.main()