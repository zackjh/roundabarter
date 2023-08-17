"""Defines utility functions."""


def format_seconds(seconds):
    """Formats seconds into days, hours, minutes, and seconds."""
    days = seconds // 86400
    seconds %= 86400

    hours = seconds // 3600
    seconds %= 3600

    minutes = seconds // 60
    seconds %= 60

    formatted_time = ""
    if days > 0:
        formatted_time += f"{days}d "
    if hours > 0:
        formatted_time += f"{hours}h "
    if minutes > 0:
        formatted_time += f"{minutes}min "
    if seconds > 0:
        formatted_time += f"{seconds}s"

    return formatted_time.strip()
