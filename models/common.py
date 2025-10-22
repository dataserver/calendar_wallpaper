import calendar
import ctypes
import platform
import subprocess
from pathlib import Path

from config.config import Config
from models.calendar_image_gen import CalendarImageGen
from utils.logger import setup_logger

logger = setup_logger(name="shared_logger")


def publish_calendar_image(
    year: int,
    month: int,
    start_of_week: str,
    update_wallpaper: bool,
):
    """
    Generates a calendar image for the given year and month,
    and optionally sets the image as the desktop wallpaper.

    Args:
        year (int): Year for the calendar (defaults to current year).
        month (int): Month for the calendar (defaults to current month).
        start_of_week (str): The first day of the week. Can be "sun" or "mon".
        should_set_wallpaper (bool): Flag to set the generated image as wallpaper.
    """

    start_weekday = calendar.SUNDAY if start_of_week == "sun" else calendar.MONDAY

    # Generate calendar image
    app = CalendarImageGen(Config)
    # Read events from DB
    events = app.read_events_db(app.cfg.EVENTS_DB_FILE)
    logger.debug(f"{year}, {month}, {events}, {start_weekday}")
    app.draw_calendar(year, month, events, start_weekday)

    # If user requested, set the calendar image as wallpaper
    if update_wallpaper:
        set_wallpaper(app.cfg.WALLPAPER_FILE)
        logger.info(f"Calendar wallpaper set as {app.cfg.WALLPAPER_FILE}")
    else:
        logger.info(f"Calendar image generated: {app.cfg.WALLPAPER_FILE}")


def set_wallpaper(image: Path) -> None:
    """
    Sets the desktop wallpaper to the specified image, based on the operating system.

    Args:
        image (Path): The absolute path to the image file to be set as wallpaper.
                       Supported formats include .bmp, .jpg, .jpeg, .png.
    """
    SUPPORTED_FORMATS = {".bmp", ".jpg", ".jpeg", ".png"}
    image_str = str(image)

    # Validate image file format
    if image.suffix.lower() not in SUPPORTED_FORMATS:
        logger.error(
            f"Error: Unsupported file format '{image.suffix}'. Supported formats are: {', '.join(SUPPORTED_FORMATS)}"
        )
        return

    # Ensure the path exists
    if not image.exists():
        logger.error(f"Error: Image file not found at '{image}'")
        return

    # Get the operating system
    os_name = platform.system().lower()

    if os_name == "windows":
        set_wallpaper_windows(image_str)
    elif os_name == "darwin":  # macOS
        set_wallpaper_macos(image_str)
    elif os_name == "linux":
        set_wallpaper_linux(image_str)
    else:
        logger.error(f"Unsupported OS: {os_name}")


def set_wallpaper_windows(image: str) -> None:
    """Sets wallpaper on Windows."""
    SPI_SETDESKWALLPAPER = 20
    SPIF_UPDATEINIFILE = 0x01
    SPIF_SENDCHANGE = 0x02
    flags = SPIF_UPDATEINIFILE | SPIF_SENDCHANGE

    # Call the SystemParametersInfoW function to set the wallpaper
    ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER,
        0,  # Not used for setting wallpaper
        image,
        flags,
    )
    logger.info(f"Desktop wallpaper set to: '{image}'")


def set_wallpaper_macos(image: str) -> None:
    """Sets wallpaper on macOS."""
    try:
        # Use AppleScript to change wallpaper
        applescript = f"""
        tell application "System Events"
            set desktop picture to POSIX file "{image}"
        end tell
        """
        subprocess.run(["osascript", "-e", applescript], check=True)
        logger.info(f"Desktop wallpaper set to: '{image}' on macOS")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to set wallpaper on macOS: {e}")


def set_wallpaper_linux(image: str) -> None:
    """Sets wallpaper on Linux (GNOME)."""
    try:
        # Use gsettings for GNOME (other desktop environments may require different tools)
        subprocess.run(
            [
                "gsettings",
                "set",
                "org.gnome.desktop.background",
                "picture-uri",
                f"file://{image}",
            ],
            check=True,
        )
        logger.info(f"Desktop wallpaper set to: '{image}' on Linux")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to set wallpaper on Linux: {e}")
        # Try using 'feh' as an alternative if gsettings fails
        try:
            subprocess.run(["feh", "--bg-scale", image], check=True)
            logger.info(f"Desktop wallpaper set to: '{image}' using 'feh' on Linux")
        except subprocess.CalledProcessError:
            logger.error("Failed to set wallpaper using 'feh' on Linux.")
