# p2app/engine/main.py
#
# ICS 33 Winter 2025
# Project 2: Learning to Fly
#
# An object that represents the engine of the application.

import sqlite3
from typing import Generator, Union

import p2app.events as events
from p2app.events import QuitInitiatedEvent


class Engine:
    """An object that represents the application's engine, whose main role is to
    process events sent to it by the user interface, then generate events that are
    sent back to the user interface in response, allowing the user interface to be
    unaware of any details of how the engine is implemented.
    """

    def __init__(self):
        """Initializes the engine"""
        self._connection = None
        self._handlers = {
            events.QuitInitiatedEvent: self._handle_quit,
            events.OpenDatabaseEvent: self._handle_open_database,
            events.CloseDatabaseEvent: self._handle_close_database,
            events.StartContinentSearchEvent: self._handle_search_continents
        }

    def process_event(self, event):
        """A generator function that processes one event sent from the user interface,
        yielding zero or more events in response."""
        event_type = type(event)

        if event_type not in self._handlers.keys():
            yield from ()
            return

        yield from self._handlers[type(event)](event)

    # event handlers

    # application-level events
    def _handle_quit(self, event: events.QuitInitiatedEvent) \
            -> Generator[events.EndApplicationEvent]:
        """Quits the application."""

        yield events.EndApplicationEvent()
        return

    def _handle_open_database(self, event: events.OpenDatabaseEvent) \
            -> Generator[Union[events.DatabaseOpenedEvent, events.DatabaseOpenFailedEvent]]:
        """Opens the connection to the database file."""

        if not event.path().exists():
            yield events.DatabaseOpenFailedEvent("Database does not exist.")
            return

        try:
            self._connection = sqlite3.connect(event.path())
            yield events.DatabaseOpenedEvent(event.path())
        except sqlite3.Error as e:
            yield events.DatabaseOpenFailedEvent("Failed to open database.")
        return

    def _handle_close_database(self, event: events.CloseDatabaseEvent) \
            -> Generator[events.DatabaseClosedEvent]:
        """Closes the connection to the database file."""

        self._connection.close()
        yield events.DatabaseClosedEvent()
        return

    def _handle_search_continents(self, event: events.StartContinentSearchEvent) \
            -> Generator[events.ContinentSearchResultEvent]:
        """Searches for continents by code and name."""

        cursor = self._connection.cursor()

        code = event.continent_code().upper() if event.continent_code() else None
        name = event.name()

        if code and name:
            cursor.execute(
                "SELECT * FROM continent"
                "    WHERE continent_code = :code AND name LIKE :formatted_name",
                { "code": code, "formatted_name": f"%{ name }%" })

        elif code:
            cursor.execute("SELECT * FROM continent WHERE continent_code = :code",
                           { "code": code })

        elif name:
            cursor.execute("SELECT * FROM continent WHERE name LIKE :formatted_name",
                           { "formatted_name": f"%{ name }%" })

        else:
            cursor.execute("SELECT * FROM continent")

        for row in cursor:
            yield events.ContinentSearchResultEvent(events.Continent(*row))
        return