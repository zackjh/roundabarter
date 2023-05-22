"""Defines function decorators that are used for Roundabarter Bot."""

from functools import wraps
import json
import os

from telegram import Update
from telegram.ext import (
    ContextTypes,
)

# Get environment variables
LIST_OF_ADMINS = json.loads(os.environ["LIST_OF_ADMINS"])


def restricted(func):
    """Restricts usage of 'func' to user IDs in the 'LIST_OF_ADMINS' array."""

    @wraps(func)
    async def wrapped(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        user_id = update.effective_user.id
        if user_id not in LIST_OF_ADMINS:
            await update.message.reply_text(
                "You do not have permission to use this bot."
            )
            return
        return await func(update, context, *args, **kwargs)

    return wrapped
