import calendar
import sqlite3
from datetime import datetime, timedelta

from PIL import Image, ImageDraw, ImageFont

from utils.logger import setup_logger
from utils.shared_utils import hex_to_rgb

logger = setup_logger(name="imagegen_logger")


class CalendarImageGen:
    def __init__(self, config):
        # Load config and convert hex colors to RGB
        self.cfg = config
        self.cfg.BACKGROUND_COLOR = hex_to_rgb(config.BACKGROUND_COLOR)
        self.cfg.TEXT_COLOR = hex_to_rgb(config.TEXT_COLOR)
        self.cfg.EVENT_COLOR = hex_to_rgb(config.EVENT_COLOR)
        self.cfg.GRID_COLOR = hex_to_rgb(config.GRID_COLOR)
        self.cfg.TODAY_CELL_BG_COLOR = hex_to_rgb(config.TODAY_CELL_BG_COLOR)
        self.cfg.TODAY_EVENT_COLOR = hex_to_rgb(config.TODAY_EVENT_COLOR)

    # ------------- READ EVENTS ----------------
    def read_events_db(
        self, db_path: str | None = None
    ) -> dict[datetime.date, list[str]]:
        """
        Reads events from an SQLite database and returns them in a dictionary format.
        """
        events: dict[datetime.date, list[str]] = {}

        try:
            if not db_path:
                db_path = self.cfg.EVENTS_DB_FILE

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT event_datetime, title FROM events")
            rows = cursor.fetchall()
            for date_str, title in rows:
                try:
                    dt = datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M")
                    event_list = events.setdefault(dt.date(), [])
                    if dt.strftime("%H:%M") == "00:00":
                        event_list.append(title.strip())
                    else:
                        event_list.append(f"{dt.strftime('%H:%M')} - {title.strip()}")
                except ValueError:
                    logger.error(f"⚠️ Invalid datetime format in DB: {date_str}")

            conn.close()
            logger.info(f"Events read from database: {db_path}")
        except Exception as e:
            logger.error(f"Failed to read events from database: {db_path}. Error: {e}")
        return events

    # ------------- CALENDAR GRID GENERATION ----------------
    def generate_calendar_grid(
        self, year: int, month: int, start_of_week: int
    ) -> list[list[datetime.date]]:
        """
        Generates a 6x7 grid of datetime.date objects for the calendar.
        Days outside the target month are represented as actual dates from adjacent months.
        Returns a list of 6 weeks, each with 7 days (dates).
        """
        # Set the first weekday
        cal = calendar.Calendar(firstweekday=start_of_week)
        # Get all days in the month as date objects
        month_dates = cal.itermonthdates(year, month)
        # This returns ~6 weeks of dates, including prev/next month
        all_dates = list(month_dates)

        min_days = self.cfg.CALENDAR_MIN_NUM_ROWS * 7  # e.g., 6 * 7 = 42

        if len(all_dates) < min_days:
            # Pad with next month days until we reach min_days
            last_date = all_dates[-1]
            while len(all_dates) < min_days:
                last_date += timedelta(days=1)
                all_dates.append(last_date)
        # If >= min_days, use as-is (no truncation)

        # Split into weeks
        weeks = []
        for i in range(0, len(all_dates), 7):
            week = all_dates[i : i + 7]
            # Ensure every week has exactly 7 days (should always be true)
            if len(week) == 7:
                weeks.append(week)
            else:
                # Safety: pad incomplete final week (shouldn't happen)
                while len(week) < 7:
                    week.append(week[-1] + timedelta(days=1))
                weeks.append(week)

        return weeks

    # ------------- DRAW CALENDAR ----------------
    def draw_calendar(
        self,
        year: int,
        month: int,
        events: dict[datetime.date, list[str]],
        start_of_week: int,
    ) -> None:
        """
        Generates a calendar image for the specified month and year, including events.
        """
        logger.info(f"Generating calendar for {calendar.month_name[month]} {year}.")
        calendar.setfirstweekday(start_of_week)

        # Get today's date for highlighting
        today = datetime.today().date()

        # Create image
        calendar_image = Image.new(
            "RGB",
            (self.cfg.IMG_WIDTH, self.cfg.IMG_HEIGHT),
            self.cfg.BACKGROUND_COLOR,
        )
        draw = ImageDraw.Draw(calendar_image)

        # Load fonts
        title_font, day_font, event_font = self.load_fonts()

        # 1. Draw title
        month_year_title = f"{calendar.month_name[month]} {year}"
        title_width, title_height = self.get_text_size(
            draw, month_year_title, title_font
        )
        title_position = (
            (self.cfg.IMG_WIDTH - title_width) / 2,
            self.cfg.MARGIN_TOP,
        )
        draw.text(
            title_position,
            month_year_title,
            fill=self.cfg.TEXT_COLOR,
            font=title_font,
        )

        # 2. Generate 6-week date grid
        date_grid = self.generate_calendar_grid(year, month, start_of_week)
        num_rows = len(date_grid)

        # 3. Calculate cell dimensions (always 6 rows)
        cell_width = (
            self.cfg.IMG_WIDTH - self.cfg.MARGIN_LEFT - self.cfg.MARGIN_RIGHT
        ) / 7
        cell_height = (
            self.cfg.IMG_HEIGHT - self.cfg.MARGIN_TOP - self.cfg.MARGIN_BOTTOM - 100
        ) / num_rows  # Use actual row count (≥ MIN)

        # 4. Draw weekday headers
        self.draw_weekday_headers(draw, day_font, cell_width, start_of_week)

        # 5. Draw day boxes and events
        self.draw_day_boxes_and_events(
            draw,
            year,
            month,
            date_grid,
            events,
            cell_width,
            cell_height,
            day_font,
            event_font,
            today,  # Pass today's date for comparison
        )

        # 6. Save image
        calendar_image.save(self.cfg.WALLPAPER_FILE)
        logger.info(f"✅ Calendar image saved as {self.cfg.WALLPAPER_FILE}")

    def load_fonts(
        self,
    ) -> tuple[ImageFont.ImageFont, ImageFont.ImageFont, ImageFont.ImageFont]:
        """
        Loads the fonts safely for the calendar image.
        """
        try:
            title_font = ImageFont.truetype(
                self.cfg.FONT_FILE, self.cfg.MONTH_TITLE_FONT_SIZE
            )
            day_font = ImageFont.truetype(self.cfg.FONT_FILE, self.cfg.DAY_FONT_SIZE)
            event_font = ImageFont.truetype(
                self.cfg.FONT_FILE, self.cfg.EVENT_FONT_SIZE
            )
        except Exception:  # In case fonts fail to load, use default fonts
            title_font = ImageFont.load_default()
            day_font = ImageFont.load_default()
            event_font = ImageFont.load_default()
            logger.warning("Fonts could not be loaded. Using default fonts.")

        return title_font, day_font, event_font

    def get_text_size(
        self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont
    ) -> tuple[int, int]:
        """
        Calculates the width and height of the text using the given font.
        """
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            return draw.textsize(text, font=font)

    def draw_weekday_headers(
        self,
        draw: ImageDraw.ImageDraw,
        day_font: ImageFont.ImageFont,
        cell_width: float,
        start_of_week: int,
    ) -> None:
        """
        Draws the weekday headers (Mon, Tue, ..., Sun) on the calendar.
        """
        weekdays = []
        for i in range(7):
            day_index = (start_of_week + i) % 7
            weekdays.append(calendar.day_abbr[day_index])

        for i, day_name in enumerate(weekdays):
            x = self.cfg.MARGIN_LEFT + i * cell_width + 20
            draw.text(
                (x + 20, self.cfg.MARGIN_TOP + 60),
                day_name,
                fill=self.cfg.TEXT_COLOR,
                font=day_font,
            )

    def wrap_text(
        self, text: str, max_pixel_width: float, font: ImageFont.ImageFont
    ) -> list[str]:
        """
        Wrap text into multiple lines so that each line fits within the given pixel width.
        """
        draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]

            if line_width <= max_pixel_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word  # Start a new line with the current word

        if current_line:
            lines.append(current_line)

        return lines

    def draw_day_boxes_and_events(
        self,
        draw: ImageDraw.ImageDraw,
        year: int,
        month: int,
        date_grid: list[list[datetime.date]],
        event_dict: dict[datetime.date, list[str]],
        cell_width: float,
        cell_height: float,
        day_font: ImageFont.ImageFont,
        event_font: ImageFont.ImageFont,
        today: datetime.date,
    ) -> None:
        """
        Draws calendar cells using actual datetime.date objects.
        Handles current/adjacent months and event rendering.
        """
        for week_idx, week_dates in enumerate(date_grid):
            for day_idx, actual_date in enumerate(week_dates):
                cell_left = self.cfg.MARGIN_LEFT + day_idx * cell_width
                cell_top = self.cfg.MARGIN_TOP + 100 + week_idx * cell_height
                cell_right = cell_left + cell_width
                cell_bottom = cell_top + cell_height

                in_current_month = (
                    actual_date.year == year and actual_date.month == month
                )
                is_current_day = actual_date == today

                # Draw cell background
                if is_current_day:
                    draw.rectangle(
                        [cell_left, cell_top, cell_right, cell_bottom],
                        fill=self.cfg.TODAY_CELL_BG_COLOR,
                        outline=self.cfg.GRID_COLOR,
                        width=2,
                    )
                else:
                    draw.rectangle(
                        [cell_left, cell_top, cell_right, cell_bottom],
                        outline=self.cfg.GRID_COLOR,
                        width=2,
                    )

                # Draw day number
                day_text_color = (
                    self.cfg.TEXT_COLOR
                    if in_current_month
                    else tuple(max(0, int(c * 0.5)) for c in self.cfg.TEXT_COLOR)
                )
                draw.text(
                    (cell_left + 7, cell_top + 5),
                    str(actual_date.day),
                    fill=day_text_color,
                    font=day_font,
                )

                # Draw events
                if actual_date in event_dict:
                    event_y_position = cell_top + 25
                    event_x_offset = 10
                    max_event_width = cell_width - 20
                    fill_color = (
                        self.cfg.TODAY_EVENT_COLOR
                        if is_current_day
                        else self.cfg.EVENT_COLOR
                    )
                    # Dim events for non-current-month days (unless it's today)
                    if not in_current_month and not is_current_day:
                        fill_color = tuple(max(0, int(c * 0.6)) for c in fill_color)

                    for event in event_dict[actual_date]:
                        wrapped_lines = self.wrap_text(
                            event, max_event_width, event_font
                        )
                        for line in wrapped_lines:
                            if event_y_position + 12 > cell_bottom:
                                logger.warning(
                                    f"Event text overflowed in cell: {actual_date}."
                                )
                                break
                            draw.text(
                                (cell_left + event_x_offset, event_y_position),
                                line,
                                fill=fill_color,
                                font=event_font,
                            )
                            event_y_position += 12
                        if event_y_position + 12 > cell_bottom:
                            break
