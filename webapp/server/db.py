"""
setup.py
    initialize sqlite database if it does not exist.
    create required tables
"""
# Standard Library
import logging
import os
import sqlite3

logger = logging.getLogger('app.db')

APP_DB = 'data.sqlite3'


def dict_factory(cursor, row):
    """get results as dictionary from db"""
    return dict((col[0], row[idx]) for idx, col in enumerate(cursor.description))

def add_to_queue(item_name):
    """ Add an item to queue"""
    connection = sqlite3.connect(APP_DB)
    cursor = connection.cursor()
    cursor.execute('INSERT INTO queue (name) VALUES (?)', (item_name,))
    queue_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return queue_id

def setup():
    """Initial setup for the application.  Checks if the sqlite database file is present.
    if not, create the database, and initialize the table structures
    """
    queries = [
        """
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT CHECK(status IN ('Queued', 'In Progress', 'Done')) NOT NULL DEFAULT 'Queued'
        )
        """,
    ]

    if not os.path.isfile(APP_DB):
        connection = sqlite3.connect(APP_DB)
        logger.info('Creating Default DB entries')
        for query in queries:
            logger.info(query)
            connection.execute(query)
        connection.commit()
        connection.close()
