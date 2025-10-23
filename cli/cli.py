import argparse
from datetime import datetime

from models.common import publish_calendar_image
from utils.logger import setup_logger

logger = setup_logger(name="cli_logger")


def parse_args():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Generate a calendar image with events"
    )
    opt = parser.add_argument
    opt(
        "-y",
        "--year",
        type=int,
        default=datetime.today().year,
        help="Year for the calendar",
    )
    opt(
        "-m",
        "--month",
        type=int,
        choices=range(1, 13),
        default=datetime.today().month,
        help="Month for the calendar",
    )
    opt(
        "-s",
        "--start-of-week",
        choices=["mon", "sun"],
        default="sun",
        help="Start of week: 'mon' for Monday, 'sun' for Sunday (default: sun)",
    )
    opt(
        "-w",
        "--wallpaper",
        action="store_true",  # No need to pass a value, just the presence of the flag sets it to True
        help="Set as wallpaper?",
    )
    opt(
        "-d",
        "--database",
        default="events.sqlite3",
        help="Path to SQLite database file",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    publish_calendar_image(
        year=args.year,
        month=args.month,
        start_of_week=args.start_of_week,
        update_wallpaper=args.wallpaper,
    )
