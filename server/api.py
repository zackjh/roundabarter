"""Defines API routes."""

import re
from flask import Flask, request
import db
import scraper

app = Flask(__name__)

# Create 'tracked_searches' table if it does not exist
db.create_tracked_searches_table()

# Create 'listings' table if it does not exist
db.create_listings_table()


@app.route("/new-tracked-search", methods=["POST"])
def new_tracked_search():
    """Adds a new tracked search to the database."""

    # Get POST request data
    tracked_search_name = request.form["tracked_search_name"]
    tracked_search_url = request.form["tracked_search_url"]

    # Validate that the given tracked search URL is a valid Carousell URL
    if not re.search("^https://www.carousell.sg/search/", tracked_search_url):
        # Return error response
        return ("The given search URL is not a valid Carousell search URL.", 400)

    # Verify that the given tracked search name is unique
    current_tracked_search_names = db.get_tracked_search_names()
    if tracked_search_name in current_tracked_search_names:
        # The given tracked search name already exists in 'tracked_searches' table
        # Return error response
        return ("The given search name is already in use.", 400)

    # Insert a new record into the 'tracked_searches' table
    db.insert_tracked_search(tracked_search_name, tracked_search_url)

    # Get latest listings for this tracked search
    latest_listings = scraper.scrape_latest_listings(tracked_search_url)

    # Insert new records into the 'listings' table
    for listing in latest_listings:
        db.insert_listing(
            listing["url"],
            listing["title"],
            listing["price"],
            listing["username"],
            tracked_search_name,
        )

    # Return success response
    return ("New tracked search added to the database.", 201)


@app.route("/get-latest-listings/<tracked_search_name>", methods=["PUT"])
def get_latest_listings(tracked_search_name):
    """Returns the latest listings of a tracked search"""

    # Get all the tracked search names that are in the 'tracked_searches' table
    valid_tracked_search_names = db.get_tracked_search_names()

    # Verify that the given tracked search name is a pre-existing one
    # in the 'tracked_searches' table
    if tracked_search_name not in valid_tracked_search_names:
        # Tracked search name is invalid as it doesn't exist in the 'tracked_searches' table
        # Return error response
        return (
            f"The search '{tracked_search_name}' is not currently being tracked.",
            400,
        )

    # Get the given tracked search name's corresponding tracked search URL
    tracked_search_url = db.get_tracked_search_url_by_name(tracked_search_name)

    # Run the scraper to get the latest listings of this tracked search
    latest_listings = scraper.scrape_latest_listings(tracked_search_url)

    # Delete the records for the current listings of this tracked search that are
    # already in the 'listings' table
    db.delete_listing(tracked_search_name)

    # Insert records of the latest listings into the 'listings' table
    for listing in latest_listings:
        db.insert_listing(
            listing["url"],
            listing["title"],
            listing["price"],
            listing["username"],
            tracked_search_name,
        )

    # Return success response
    return (latest_listings, 200)


@app.route("/get-new-listings/<tracked_search_name>", methods=["PUT"])
def get_new_listings(tracked_search_name):
    """Returns the new listings, if any, of a tracked search."""

    # Get the given tracked search name's corresponding tracked search URL
    tracked_search_url = db.get_tracked_search_url_by_name(tracked_search_name)

    # Run the scraper to get the latest listings of this tracked search
    latest_listings = scraper.scrape_latest_listings(tracked_search_url)

    # Get the URLs of all current listings of this tracked search from the 'listings' table
    current_listing_urls = db.get_listing_urls_by_tracked_search_name(
        tracked_search_name
    )

    # Check if the URL of each latest listing is the URL of any of the current listings
    # to determine if a latest listing is a new listing
    new_listings = []
    for latest_listing in latest_listings:
        if latest_listing["url"] not in current_listing_urls:
            # The URL of this latest listing is not a URL of any of the current listings
            # indiciating that this latest listing is a new listing
            new_listings.append(latest_listing)

    # Check if there are any new listings
    if len(new_listings) == 0:
        # There are no new listings

        # Return no data response
        return (
            f"There are no new listings for the search '{tracked_search_name}'",
            204,
        )

    # There is at least one new listing
    # Delete the records for the current listings of this tracked search that are
    # already in the 'listings' table
    db.delete_listing(tracked_search_name)

    # Insert records of the latest listings into the 'listings' table
    for listing in latest_listings:
        db.insert_listing(
            listing["url"],
            listing["title"],
            listing["price"],
            listing["username"],
            tracked_search_name,
        )

    # Return success response
    return (new_listings, 200)


@app.route("/get-tracked-searches", methods=["GET"])
def get_tracked_searches():
    """Returns information of all tracked searches."""

    # Get information of all tracked searches
    tracked_searches = db.get_tracked_searches()

    if len(tracked_searches) == 0:
        # No tracked searches in database

        # Return response
        return ("No searches are currently being tracked", 204)

    # Return success response
    return (tracked_searches, 200)


@app.route("/delete-tracked-search/<tracked_search_name>", methods=["DELETE"])
def delete_tracked_search(tracked_search_name):
    """Deletes a tracked search."""

    # Get all the tracked search names that are in the 'tracked_searches' table
    valid_tracked_search_names = db.get_tracked_search_names()

    # Verify that the given tracked search name is a pre-existing one
    # in the 'tracked_searches' table
    if tracked_search_name not in valid_tracked_search_names:
        # Tracked search name is invalid as it doesn't exist in the 'tracked_searches' table
        # Return error response
        return (
            f"The search '{tracked_search_name}' is not currently being tracked.",
            400,
        )

    # Delete the tracked search
    db.delete_tracked_search(tracked_search_name)

    # Delete the tracked search's listings
    db.delete_listing(tracked_search_name)

    # Return success response
    return (f"The search '{tracked_search_name}' has been deleted.", 200)
