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

def get_queue_item(queue_id):
    """ Get a queue item from table"""
    connection = sqlite3.connection(APP_DB)
    connection.row_factory = dict_factory
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, status FROM queue WHERE id = ?", (queue_id,))
    resultset = cursor.fetchone()
    connection.close()
    return resultset

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
