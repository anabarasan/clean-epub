"""
setup.py
    initialize sqlite database if it does not exist.
    create required tables
"""
# Standard Library
import logging
import os
import sqlite3

# app imports
from app import APP_DB


logger = logging.getLogger('app.db')


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
