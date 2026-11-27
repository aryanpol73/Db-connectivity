"""
db.py - Database connection layer.
All communication between Python and MySQL happens through this file.
"""
import os
import mysql.connector

# Change these values to match your own MySQL installation
# (or set them as environment variables).
DB_CONFIG = {
    "host":     os.environ.get("DB_HOST", "localhost"),
    "user":     os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "root"),
    "database": os.environ.get("DB_NAME", "library_db"),
}


def get_connection():
    """Open and return a new connection to the MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)


def fetch_all(query, params=()):
    """Run a SELECT query and return all rows as a list of dictionaries."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def fetch_one(query, params=()):
    """Run a SELECT query and return only the first row (or None)."""
    rows = fetch_all(query, params)
    return rows[0] if rows else None


def execute(query, params=()):
    """Run an INSERT / UPDATE / DELETE query and save (commit) the change."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    cursor.close()
    conn.close()
