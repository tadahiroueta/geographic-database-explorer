# p2app/engine/main.py
#
# ICS 33 Winter 2025
# Project 2: Learning to Fly
#
# An object that represents the engine of the application.

import sqlite3

import p2app.events as events


class Engine:
    """An object that represents the application's engine, whose main role is to
    process events sent to it by the user interface, then generate events that are
    sent back to the user interface in response, allowing the user interface to be
    unaware of any details of how the engine is implemented.
    """

    def __init__(self):
        """Initializes the engine"""
        self._connection = None


    def process_event(self, event):
        """A generator function that processes one event sent from the user interface,
        yielding zero or more events in response."""

        if type(event) == events.OpenDatabaseEvent:
            if not event.path().exists():
                yield events.DatabaseOpenFailedEvent("Database does not exist.")
                return

            try:
                self._connection = sqlite3.connect(event.path())
                yield events.DatabaseOpenedEvent(event.path())
            except sqlite3.Error as e:
                yield events.DatabaseOpenFailedEvent("Failed to open database.")
            return