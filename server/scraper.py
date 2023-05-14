"""Defines Carousell scraper functions."""

import re
from bs4 import BeautifulSoup
import requests


def scrape_latest_listings(url, number_of_listings=5):
    """Scrapes and returns the listing data of the latest listings from the specified URL."""
    response = requests.get(url, timeout=3)

    soup = BeautifulSoup(response.text, "lxml")

    listing_cards = soup.main.find_all(
        attrs={"data-testid": re.compile(r"^listing-card-\d")}
    )

    latest_listing_data = []

    for listing_card in listing_cards[0:number_of_listings]:
        p_tags = listing_card.find_all("p")

        p_tags_data = list(map(lambda p_tag: p_tag.string, p_tags))

        if p_tags_data[2] != "Protection":
            p_tags_data.insert(2, "No Protection")

        a_tags = listing_card.find_all("a")

        a_tags_data = list(
            map(lambda a_tag: f"https://www.carousell.sg{a_tag['href']}", a_tags)
        )

        url = get_simple_listing_url(a_tags_data[1])

        listing_data = {
            "username": p_tags_data[0],
            "date": p_tags_data[1],
            "protection": p_tags_data[2],
            "title": p_tags_data[3],
            "price": p_tags_data[4],
            "description": p_tags_data[5],
            "seller_profile_url": a_tags_data[0],
            "url": url,
        }

        latest_listing_data.append(listing_data)

    return latest_listing_data


def get_simple_listing_url(original_url):
    """Simplfies a Carousell listing URL by using only the listing ID."""
    original_url_reversed = original_url[::-1]

    listing_id = ""
    for char in original_url_reversed:
        if char == "-":
            break

        if char.isdigit():
            listing_id = char + listing_id

    return f"https://www.carousell.sg/p/{listing_id}/"
