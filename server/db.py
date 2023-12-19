"""Defines database methods."""

import os
import sqlite3

# Get environment variables
DATABASE_LOCATION = os.environ["DATABASE_LOCATION"]


def connect_to_db():
    """Establishes a connection to the database and returns that connection."""

    conn = sqlite3.connect(DATABASE_LOCATION)
    conn.row_factory = sqlite3.Row
    return conn


def create_tracked_searches_table():
    """Creates the 'tracked_searches' table if it doesn't exist."""
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(
        """
            CREATE TABLE IF NOT EXISTS tracked_searches (
                tracked_search_name TEXT PRIMARY KEY NOT NULL,
                tracked_search_url TEXT NOT NULL,
                scrape_interval INTEGER NOT NULL
            )
        """
    )
    conn.commit()
    conn.close()


def insert_tracked_search(tracked_search_name, tracked_search_url, scrape_interval):
    """Inserts a record into the 'tracked_searches' table."""
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(
        """
            INSERT INTO tracked_searches
            VALUES (?, ?, ?)
        """,
        (tracked_search_name, tracked_search_url, scrape_interval),
    )
    conn.commit()
    conn.close()


def get_tracked_searches():
    """Returns all records in the 'tracked_searches' table."""
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(
        """
            SELECT *
            FROM tracked_searches
        """
    )
    rows = cur.fetchall()
    tracked_searches = []
    for row in rows:
        tracked_searches.append(
            {
                "tracked_search_name": row["tracked_search_name"],
                "tracked_search_url": row["tracked_search_url"],
                "scrape_interval": int(row["scrape_interval"]),
            }
        )
    conn.close()
    return tracked_searches


def get_tracked_search_names():
    """Returns the 'tracked_search_name' field of all records in the 'tracked_searches' table."""
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(
        """
            SELECT tracked_search_name
            FROM tracked_searches
        """
    )
    rows = cur.fetchall()
    tracked_search_names = []
    for row in rows:
        tracked_search_names.append(row["tracked_search_name"])
    conn.close()
    return tracked_search_names


def get_tracked_search_url_by_name(tracked_search_name):
    """Returns the 'tracked_search_url' field of the record in the 'tracked_searches' table which has the matching 'tracked_search_name'."""
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(
        """
            SELECT tracked_search_url
            FROM tracked_searches
            WHERE tracked_search_name = ?
        """,
        (tracked_search_name,),
    )
    row = cur.fetchone()
    conn.close()
    return row["tracked_search_url"]


def update_tracked_search_scrape_interval(tracked_search_name, new_scrape_interval):
    """Updates the 'scrape_interval' field of the record in the 'tracked_searches' table which has the matching 'tracked_search_name'."""
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(
        """
            UPDATE tracked_searches
            SET scrape_interval = ?
            WHERE tracked_search_name = ?
        """,
        (new_scrape_interval, tracked_search_name),
    )
    conn.commit()
    conn.close()


def delete_tracked_search(tracked_search_name):
    """Deletes the record in the 'tracked_searches' table which has the matching 'tracked_search_name'."""
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(
        """
            DELETE
            FROM tracked_searches
            WHERE tracked_search_name = ?
        """,
        (tracked_search_name,),
    )
    conn.commit()
    conn.close()


def drop_tracked_searches_table():
    """Drops the 'tracked_searches' table."""
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(
        """
            DROP TABLE tracked_searches
        """
    )
    conn.commit()
    conn.close()


def create_listings_table():
    """Creates the 'listings' table if it doesn't exist."""
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(
        """
            CREATE TABLE IF NOT EXISTS listings (
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                price TEXT NOT NULL,
                username TEXT NOT NULL,
                tracked_search_name TEXT NOT NULL,
                PRIMARY KEY (url, tracked_search_name)
                FOREIGN KEY(tracked_search_name) REFERENCES tracked_searches(name)
            )
        """
    )
    conn.commit()
    conn.close()


def insert_listing(url, title, price, username, tracked_search_name):
    """Inserts a record into the 'listings' table."""
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(
        """
            INSERT INTO listings
            VALUES (?, ?, ?, ?, ?)
        """,
        (url, title, price, username, tracked_search_name),
    )
    conn.commit()
    conn.close()


def get_listings_by_tracked_search_name(tracked_search_name):
    """Returns all records in the 'listings' table which have the matching 'tracked_search_name'."""
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(
        """
            SELECT url, title, price, username
            FROM listings
            WHERE tracked_search_name = ?
        """,
        (tracked_search_name,),
    )
    rows = cur.fetchall()
    listings = []
    for row in rows:
        listings.append(
            {
                "url": row["url"],
                "title": row["title"],
                "price": row["price"],
                "username": row["username"],
            }
        )
    conn.close()
    return listings


def get_listing_urls_by_tracked_search_name(tracked_search_name):
    """Returns the 'url' field of all records in the 'listings' table which have the matching 'tracked_search_name'."""
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(
        """
            SELECT url
            FROM listings
            WHERE tracked_search_name = ?
        """,
        (tracked_search_name,),
    )
    rows = cur.fetchall()
    urls = []
    for row in rows:
        urls.append(row["url"])
    conn.close()
    return urls


def delete_listing(tracked_search_name):
    """Deletes all records in the 'listings' table which have the matching 'tracked_search_name'."""
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(
        """
            DELETE FROM listings
            WHERE tracked_search_name = ?
        """,
        (tracked_search_name,),
    )
    conn.commit()
    conn.close()


def drop_listings_table():
    """Drops the 'listings' table."""
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(
        """
            DROP TABLE listings
        """
    )
    conn.commit()
    conn.close()
