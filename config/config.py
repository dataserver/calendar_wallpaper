import logging
from pathlib import Path

APP_DIR = Path(__file__).parent.parent


class BaseConfig:
    IMG_WIDTH: int = 1920
    IMG_HEIGHT: int = 1080

    # Calendar margins (in pixels)
    MARGIN_TOP: int = 50
    MARGIN_BOTTOM: int = 450
    MARGIN_LEFT: int = 500
    MARGIN_RIGHT: int = 500

    # Calendar settings
    CALENDAR_MIN_NUM_ROWS = 6

    # colors can be a HEXA value or RGB tuple
    BACKGROUND_COLOR: str | tuple = "#000000"  # wallpaper background
    GRID_COLOR: str | tuple = "#141414"

    TEXT_COLOR: str | tuple = "#FFFFFF"
    EVENT_COLOR: str | tuple = "#646464"
    TODAY_CELL_BG_COLOR: str | tuple = (
        "#0F0F0F"  # Background color for the current day cell
    )
    TODAY_EVENT_COLOR: str | tuple = (
        "#E0E0E0"  # Text color for the events on current day cell
    )

    FONT_FILE: Path = (
        APP_DIR / "fonts" / "Roboto" / "Roboto-Regular.ttf"
    )  # Change to a valid font path if needed

    MONTH_TITLE_FONT_SIZE: int = 16
    DAY_FONT_SIZE: int = 16  # Default day text size
    EVENT_FONT_SIZE: int = 11

    EVENTS_DB_FILE: Path = APP_DIR / "db" / "events.sqlite3"
    WALLPAPER_FILE: Path = APP_DIR / "output" / "calendar.png"
    LOG_FILE: Path = APP_DIR / "output" / "app.log"

    LOGGING_LEVEL: int = logging.CRITICAL


class ProdConfig(BaseConfig):
    """Config production"""

    LOGGING_LEVEL: int = logging.ERROR


class DevConfig(BaseConfig):
    """Configuration for development environment"""

    LOGGING_LEVEL: int = logging.DEBUG
    EVENTS_DB_FILE: Path = APP_DIR / ".dev" / "dev.sqlite3"


Config: BaseConfig = ProdConfig

__all__ = ["Config"]
