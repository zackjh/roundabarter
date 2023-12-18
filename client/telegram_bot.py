"""Defines the behaviour of the Roundabarter Telegram bot."""

import logging
import os
import requests

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
)

from decorators import restricted

from utils import format_seconds

# Get environment variables
TELEGRAM_BOT_API_TOKEN = os.environ["TELEGRAM_BOT_API_TOKEN"]
FLASK_API_URL = os.environ["FLASK_API_URL"]
DEFAULT_SCRAPE_INTERVAL = int(os.environ["DEFAULT_SCRAPE_INTERVAL"])

# Set up app logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initialises the bot."""

    # API Call to get all tracked search names
    response = requests.get(f"{FLASK_API_URL}/get-tracked-searches", timeout=3)

    if response.status_code == 400:
        # An error occurred on the back-end
        # Reply the user with the API response's error message
        await update.message.reply_text(response.text)

    elif response.status_code == 200:
        # Tracked searches successfully received

        # Get the data of the tracked_searches in JSON format
        tracked_searches = response.json()

        # Get the tracked search names of all currently scheduled jobs
        job_tracked_search_names = [job.data for job in context.job_queue.jobs()]

        for tracked_search in tracked_searches:
            if tracked_search["tracked_search_name"] not in job_tracked_search_names:
                # There is no job scheduled for this tracked search

                # Add the 'check_for_new_listings' job to the job queue
                context.job_queue.run_repeating(
                    check_for_new_listings,
                    interval=tracked_search["scrape_interval"],
                    first=tracked_search["scrape_interval"],
                    data=tracked_search["tracked_search_name"],
                    chat_id=update.message.chat_id,
                )

    # Reply the user
    await update.message.reply_text("Roundabarter bot is running.")


@restricted
async def new_tracked_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets up a new tracked search."""

    # Validate that there are at least two arguments
    if len(context.args) < 2:
        # Reply the user with an error message
        await update.message.reply_text(
            "Please enter the name and the URL of a search."
        )

    else:
        # Concatenate all arguments except the last argument with whitespaces
        # to get the user's intended tracked search name
        tracked_search_name = " ".join(context.args[:-1])

        # Get the last argument which is the user's intended tracked search URL
        tracked_search_url = context.args[-1]

        # API call to add this tracked search to the database
        response = requests.post(
            f"{FLASK_API_URL}/new-tracked-search",
            data={
                "tracked_search_name": tracked_search_name,
                "tracked_search_url": tracked_search_url,
                "scrape_interval": DEFAULT_SCRAPE_INTERVAL,
            },
            timeout=3,
        )

        if response.status_code == 400:
            # An error occurred on the back-end
            # Reply the user with the API response's error message
            await update.message.reply_text(response.text)

        elif response.status_code == 201:
            # Data sucessfully added to the database

            # Add the 'check_for_new_listings' job to the job queue
            context.job_queue.run_repeating(
                check_for_new_listings,
                interval=DEFAULT_SCRAPE_INTERVAL,
                first=DEFAULT_SCRAPE_INTERVAL,
                data=tracked_search_name,
                chat_id=update.message.chat_id,
            )

            # Reply the user with a success message
            await update.message.reply_text(
                f"The search '{tracked_search_name}' is now being tracked."
            )


async def check_for_new_listings(context: ContextTypes.DEFAULT_TYPE):
    """Sends a message to the user if there are any new listings for a given tracked search."""

    # Get tracked search name from Job object
    tracked_search_name = context.job.data

    # API call to get any new listings for this tracked search
    response = requests.put(
        f"{FLASK_API_URL}/get-new-listings/{tracked_search_name}",
        timeout=3,
    )

    if response.status_code == 400:
        # An error occurred on the back-end
        # Create the error message that the bot will send to the user
        error_message = (
            "An error occurred while performing the periodic scrape.\n"
            f"API Response Error Message: {response.text}\n"
        )
        # Send user the error message
        await context.bot.send_message(chat_id=context.job.chat_id, text=error_message)

    elif response.status_code == 200:
        # New listings successfully retrieved

        # Get the data of the new listings in JSON format
        new_listings = response.json()

        # Create the message that the bot will reply the user with
        new_listings_message = (
            f"<i>There are {len(new_listings)} new listings for the search '{tracked_search_name}'!</i>\n"
            if len(new_listings) > 1
            else f"<i>There is 1 new listing for the search '{tracked_search_name}'!</i>\n"
        )
        for listing in new_listings:
            price = listing["price"]
            if price != "FREE":
                price = price[1:]

            new_listings_message += (
                f"{price} - <a href='{listing['url']}'>{listing['title']}</a>\n"
            )

        # Reply the user
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text=new_listings_message,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )


@restricted
async def get_latest_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Returns the latest listings of a given tracked search."""

    # Validate that there is at least one argument
    if len(context.args) < 1:
        # Reply the user with an error message
        await update.message.reply_text("Please enter the name of a tracked search.")

    else:
        # Concatenate all arguments with whitespaces to get the user's intended tracked search name
        tracked_search_name = " ".join(context.args)

        # API call to get the latest listings of this tracked search
        response = requests.put(
            f"{FLASK_API_URL}/get-latest-listings/{tracked_search_name}",
            timeout=3,
        )

        if response.status_code == 400:
            # An error occurred on the back-end
            # Reply the user with the API response's error message
            await update.message.reply_text(response.text)

        elif response.status_code == 200:
            # Latest listings successfully retrieved

            # Get the data of the latest listings in JSON format
            latest_listings = response.json()

            # Create the message that the bot will reply the user with
            latest_listings_message = f"<i>Here are the {len(latest_listings)} most recent listings for the search '{tracked_search_name}':</i>\n"
            for listing in latest_listings:
                price = listing["price"]
                if price != "FREE":
                    price = price[1:]

                latest_listings_message += (
                    f"{price} - <a href='{listing['url']}'>{listing['title']}</a>\n"
                )

            # Reply the user with a success message
            await update.message.reply_text(
                latest_listings_message,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )


@restricted
async def get_tracked_searches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Returns all currently tracked searches."""

    # API Call to get all tracked search names
    response = requests.get(f"{FLASK_API_URL}/get-tracked-searches", timeout=3)

    if response.status_code == 400:
        # An error occurred on the back-end
        # Reply the user with the API response's error message
        await update.message.reply_text(response.text)

    elif response.status_code == 204:
        # No tracked searches

        # Reply the user
        await update.message.reply_text("No searches are currently being tracked.")

    elif response.status_code == 200:
        # Tracked searches successfully received

        # Get the data of the tracked_searches in JSON format
        tracked_searches = response.json()

        # Create the message that the bot will reply the user with
        tracked_searches_message = (
            f"<i>{len(tracked_searches)} searches are currently being tracked.</i>\n"
            if len(tracked_searches) > 1
            else "<i>1 search is currently being tracked.</i>\n"
        )
        for tracked_search in tracked_searches:
            scrape_interval_formatted = format_seconds(
                tracked_search["scrape_interval"]
            )
            tracked_searches_message += f"<a href='{tracked_search['tracked_search_url']}'>{tracked_search['tracked_search_name']}</a> ({scrape_interval_formatted})\n"

        # Reply the user
        await update.message.reply_text(
            tracked_searches_message,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )


@restricted
async def update_tracked_search_scrape_interval(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Updates the scrape interval of a tracked search."""

    # Validate that there are at least two arguments
    if len(context.args) < 2:
        # Reply the user with an error message
        await update.message.reply_text(
            "Please enter the name of a search and the new scrape interval."
        )

    else:
        # Concatenate all arguments except the last argument with whitespaces
        # to get the user's intended tracked search name
        tracked_search_name = " ".join(context.args[:-1])

        # Get the last argument which is the user's intended new scrape interval
        new_scrape_interval = context.args[-1]

        # Check if 'new_scrape_interval' is not a digit
        if not new_scrape_interval.isdigit():
            # Reply the user with an error message
            await update.message.reply_text("Please enter a valid scrape interval.")

        else:
            # Convert 'new_scrape_interval' from string to integer
            new_scrape_interval = int(new_scrape_interval)

            # API call to update the scrape interval of this tracked search in the database
            response = requests.put(
                f"{FLASK_API_URL}/update-tracked-search-scrape-interval/{tracked_search_name}",
                data={
                    "new_scrape_interval": new_scrape_interval,
                },
                timeout=3,
            )

            if response.status_code == 400:
                # An error occurred on the back-end
                # Reply the user with the API response's error message
                await update.message.reply_text(response.text)

            elif response.status_code == 200:
                # Tracked search scrape interval in database successfully updated

                # Remove the current 'check_for_new_listings' job for this tracked search from the job queue
                # Get all currently scheduled jobs
                jobs = context.job_queue.jobs()
                for job in jobs:
                    if job.data == tracked_search_name:
                        # This job is the one that runs for this tracked search
                        # Remove this job from the job queue
                        job.schedule_removal()

                # Add the new 'check_for_new_listings' job for this tracked search with the updated scrape interval to the job queue
                context.job_queue.run_repeating(
                    check_for_new_listings,
                    interval=new_scrape_interval,
                    first=new_scrape_interval,
                    data=tracked_search_name,
                    chat_id=update.message.chat_id,
                )

                # Reply the user with a success message
                await update.message.reply_text(
                    f"The scrape interval of the search '{tracked_search_name}' has been updated to {format_seconds(new_scrape_interval)}."
                )


@restricted
async def remove_tracked_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Removes a tracked search."""

    # Validate that there is at least one argument
    if len(context.args) < 1:
        # Reply the user with an error message
        await update.message.reply_text("Please enter the name of a tracked search.")

    else:
        # Concatenate all arguments with whitespaces to get the user's intended tracked search name
        tracked_search_name = " ".join(context.args)

        # API Call to delete data in the database that is related to this tracked search
        response = requests.delete(
            f"{FLASK_API_URL}/delete-tracked-search/{tracked_search_name}",
            timeout=3,
        )

        if response.status_code == 400:
            # An error occurred on the back-end
            # Reply the user with the API response's error message
            await update.message.reply_text(response.text)

        elif response.status_code == 200:
            # Tracked search data successfully deleted from database

            # Remove 'check_for_new_listings' job from the job queue
            # Get all currently scheduled jobs
            jobs = context.job_queue.jobs()
            for job in jobs:
                if job.data == tracked_search_name:
                    # This job is the one that runs for this tracked search
                    # Remove this job from the job queue
                    job.schedule_removal()

            # Reply the user with a success message
            await update.message.reply_text(
                f"The search '{tracked_search_name}' is no longer being tracked."
            )


if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_BOT_API_TOKEN).build()

    start_handler = CommandHandler("start", start)
    new_tracked_search_handler = CommandHandler("new", new_tracked_search)
    get_latest_listings_handler = CommandHandler("fetch", get_latest_listings)
    get_tracked_searches_handler = CommandHandler("list", get_tracked_searches)
    remove_tracked_search_handler = CommandHandler("remove", remove_tracked_search)
    update_tracked_search_scrape_interval_handler = CommandHandler(
        "update", update_tracked_search_scrape_interval
    )

    application.add_handler(start_handler)
    application.add_handler(new_tracked_search_handler)
    application.add_handler(get_latest_listings_handler)
    application.add_handler(get_tracked_searches_handler)
    application.add_handler(remove_tracked_search_handler)
    application.add_handler(update_tracked_search_scrape_interval_handler)

    application.run_polling()
