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

# Get environment variables
TELEGRAM_BOT_API_TOKEN = os.environ["TELEGRAM_BOT_API_TOKEN"]
FLASK_API_URL = os.environ["FLASK_API_URL"]
SCRAPE_INTERVAL = int(os.environ["SCRAPE_INTERVAL"])

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

                # Add the 'check_for_new_listings' job to the job queue and have it run every 10 seconds
                context.job_queue.run_repeating(
                    check_for_new_listings,
                    interval=SCRAPE_INTERVAL,
                    first=SCRAPE_INTERVAL,
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

        # API call to add the tracked search to the database
        response = requests.post(
            f"{FLASK_API_URL}/new-tracked-search",
            data={
                "tracked_search_name": tracked_search_name,
                "tracked_search_url": tracked_search_url,
            },
            timeout=3,
        )

        if response.status_code == 400:
            # An error occurred on the back-end
            # Reply the user with the API response's error message
            await update.message.reply_text(response.text)

        elif response.status_code == 201:
            # Data sucessfully added to the database

            # Add the 'check_for_new_listings' job to the job queue and have it run every 10 seconds
            context.job_queue.run_repeating(
                check_for_new_listings,
                interval=SCRAPE_INTERVAL,
                first=SCRAPE_INTERVAL,
                data=tracked_search_name,
                chat_id=update.message.chat_id,
            )

            # Reply the user with a success message
            await update.message.reply_text(
                f"The search '{tracked_search_name}' is now being tracked."
            )


@restricted
async def check_for_new_listings(context: ContextTypes.DEFAULT_TYPE):
    """Sends a message to the user if there are any new listings for a given tracked search."""

    # Get tracked search name from Job object
    tracked_search_name = context.job.data

    # API call to get any new listings of the tracked search
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
            new_listings_message += f"{listing['price'][1:]} - <a href='{listing['url']}'>{listing['title']}</a>\n"

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

        # API call to get the latest listings of the tracked search
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
                latest_listings_message += f"{listing['price'][1:]} - <a href='{listing['url']}'>{listing['title']}</a>\n"

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
            tracked_searches_message += f"<a href='{tracked_search['tracked_search_url']}'>{tracked_search['tracked_search_name']}</a>\n"

        # Reply the user
        await update.message.reply_text(
            tracked_searches_message,
            parse_mode="HTML",
            disable_web_page_preview=True,
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

        # API Call to delete data in the database that is related to the tracked search
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

    application.add_handler(start_handler)
    application.add_handler(new_tracked_search_handler)
    application.add_handler(get_latest_listings_handler)
    application.add_handler(get_tracked_searches_handler)
    application.add_handler(remove_tracked_search_handler)

    application.run_polling()
