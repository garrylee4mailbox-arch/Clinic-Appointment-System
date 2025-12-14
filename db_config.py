
"""
db_config.py
------------
Central place to configure and create MySQL connections.

All other modules import `get_connection()` from here.
"""

import pymysql


def get_connection():
    """
    Create and return a new MySQL connection.

    IMPORTANT:
        - Change `user`, `password`, and (if needed) `host` to match your local setup.
        - The database name should match your schema (here we assume `clinic_app`).
    """
    return pymysql.connect(
        host="localhost",
        user="root",          # TODO: change to your MySQL user
        password="1308245",   # TODO: change to your MySQL password
        database="clinic_app",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.Cursor,
    )
