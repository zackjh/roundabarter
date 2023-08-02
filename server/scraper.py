"""Defines Carousell scraper functions."""

import re
import random
from bs4 import BeautifulSoup
import requests

USER_AGENTS_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/91.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/93.0.961.47 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36",
]


def scrape_latest_listings(url, number_of_listings=5):
    """Scrapes and returns the listing data of the latest listings from the specified URL."""
    response = requests.get(
        url, headers={"User-Agent": random.choice(USER_AGENTS_LIST)}, timeout=3
    )

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
