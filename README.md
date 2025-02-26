# Geographic Database Explorer
***Desktop application to intuitively read and write to geographic SQL database***

[Built With](#built-with) · [Features](#features) · [Installation](#installation) · [Usage](#usage)

## Built With

- ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
- ![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)

## Features

### Dynamic SQL query generation

SQL queries are automatically generated with SQLite based on the user's interaction with the GUI.

![GUI](https://github.com/tadahiroueta/bridge-america/blob/main/screenshots/edit-gb.png)

      > User interface to interact with the database

```sqlite
SELECT * FROM region
   WHERE local_code = :local_code
   AND name LIKE :formatted_name
```

      > Generated SQL query

### Unit Testing

Unit tests were written to individually test the functionality of the application with near 100% coverage.

```python
def test_close_database(self):
   RANDOM_INJECTION = "SELECT * FROM sqlite_master;"
   
   for _ in self._engine._handle_open_database(events.OpenDatabaseEvent(DATABASE_PATH)):
      pass
   post_process = self._engine._handle_close_database(events.CloseDatabaseEvent())
   
   self.assertEqual(type(next(post_process)), events.DatabaseClosedEvent,
                   "Failed to send event for closing database.")
   with self.assertRaises(sqlite3.ProgrammingError, msg="Failed to actually close database."):
      self._engine._connection.execute(RANDOM_INJECTION)
```

## Installation

1. Install [Python](https://www.python.org/downloads/)

2. Clone repository
    ```sh
    git clone https://github.com/tadahiroueta/geographic-database-explorer.git
    ```
    
## Usage

1. Run the program
    ```sh
    python project2.py
    ```

2. Load database
   > File > Open > airport.db
   
3. Explore
    > Click on Edit and pick a geographic table to interact with. Feel free to search for countries, or even create one of your own! All changes are saved for later visits to the database. 