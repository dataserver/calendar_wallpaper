import calendar
import sqlite3
from datetime import datetime

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

    # ------------- DRAW CALENDAR ----------------
    def draw_calendar(
        self,
        year: int,
        month: int,
        events: dict[datetime.date, list[str]],
        start_weekday: int,
    ) -> None:
        """
        Generates a calendar image for the specified month and year, including events.
        """
        logger.info(f"Generating calendar for {calendar.month_name[month]} {year}.")
        calendar.setfirstweekday(start_weekday)

        # Get today's date for highlighting
        today = datetime.today().date()

        # Create a new blank image with the specified background color
        calendar_image = Image.new(
            "RGB",
            (self.cfg.IMG_WIDTH, self.cfg.IMG_HEIGHT),
            self.cfg.BACKGROUND_COLOR,
        )
        draw = ImageDraw.Draw(calendar_image)

        # Load the fonts required for the title, days, and events
        title_font, day_font, event_font = self.load_fonts()

        # 1. Draw the calendar title (Month Year)
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

        # 2. Set up the grid for the calendar
        month_grid = calendar.monthcalendar(year, month)

        # Calculate the width and height of each calendar cell (day box)
        cell_width = (
            self.cfg.IMG_WIDTH - self.cfg.MARGIN_LEFT - self.cfg.MARGIN_RIGHT
        ) / 7  # 7 days in a week
        cell_height = (
            self.cfg.IMG_HEIGHT - self.cfg.MARGIN_TOP - self.cfg.MARGIN_BOTTOM - 100
        ) / len(month_grid)  # Rows are weeks

        # 3. Draw the weekday headers (Mon, Tue, ..., Sun)
        self.draw_weekday_headers(draw, day_font, cell_width, start_weekday)

        # 4. Draw the day boxes (with events if any)
        self.draw_day_boxes_and_events(
            draw,
            year,
            month,
            month_grid,
            events,
            cell_width,
            cell_height,
            day_font,
            event_font,
            today,  # Pass today's date for comparison
        )

        # 5. Save the generated calendar image to a file
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
        start_weekday: int,
    ) -> None:
        """
        Draws the weekday headers (Mon, Tue, ..., Sun) on the calendar.
        """
        weekdays = []
        for i in range(7):
            day_index = (start_weekday + i) % 7
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
        month_calendar: list[list[int]],
        event_dict: dict[datetime.date, list[str]],
        cell_width: float,
        cell_height: float,
        day_font: ImageFont.ImageFont,
        event_font: ImageFont.ImageFont,
        today: datetime.date,  # Added today's date for highlighting
    ) -> None:
        """
        Draws the day boxes and event names on the calendar.
        """
        for week_idx, week_days in enumerate(month_calendar):
            for day_idx, day_of_month in enumerate(week_days):
                cell_left = self.cfg.MARGIN_LEFT + day_idx * cell_width
                cell_top = self.cfg.MARGIN_TOP + 100 + week_idx * cell_height
                cell_right = cell_left + cell_width
                cell_bottom = cell_top + cell_height

                # Determine if this cell represents today
                is_current_day = False
                if day_of_month != 0:
                    cell_date = datetime(year, month, day_of_month).date()
                    if cell_date == today:
                        is_current_day = True

                # Fill the cell background if it's the current day
                if is_current_day:
                    draw.rectangle(
                        [cell_left, cell_top, cell_right, cell_bottom],
                        fill=self.cfg.TODAY_CELL_BG_COLOR,  # Highlight background
                        outline=self.cfg.GRID_COLOR,
                        width=2,
                    )
                else:
                    # Draw only the border for non-current days
                    draw.rectangle(
                        [cell_left, cell_top, cell_right, cell_bottom],
                        outline=self.cfg.GRID_COLOR,
                        width=2,
                    )

                if (
                    day_of_month != 0
                ):  # Only draw for valid days (0 means no day in this cell)
                    date_object = datetime(year, month, day_of_month).date()
                    day_number_x_offset = 7  # Horizontal padding for the day number
                    day_number_y_offset = 5  # Vertical padding for the day number

                    # Choose text color: keep original for non-current, or enhance contrast if needed
                    day_text_color = self.cfg.TEXT_COLOR

                    # Draw the day number inside the cell
                    draw.text(
                        (
                            cell_left + day_number_x_offset,
                            cell_top + day_number_y_offset,
                        ),
                        str(day_of_month),
                        fill=day_text_color,
                        font=day_font,
                    )

                    # Check and draw events for the day
                    if date_object in event_dict:
                        event_y_position = (
                            cell_top + 25
                        )  # Vertical position for the first event
                        event_x_offset = 10  # Horizontal padding for events

                        # Maximum width for events inside the cell
                        max_event_width = (
                            cell_width - 20
                        )  # Padding for left and right edges
                        fill_color = (
                            self.cfg.TODAY_EVENT_COLOR
                            if is_current_day
                            else self.cfg.EVENT_COLOR
                        )
                        for event in event_dict[date_object]:
                            # Wrap the event text to fit within the cell width
                            wrapped_event = self.wrap_text(
                                event, max_event_width, event_font
                            )

                            # Draw each wrapped line within the same day cell
                            for line in wrapped_event:
                                draw.text(
                                    (cell_left + event_x_offset, event_y_position),
                                    line,
                                    fill=fill_color,
                                    font=event_font,
                                )
                                event_y_position += (
                                    12  # Vertical spacing between event text lines
                                )

                            # Ensure events don't overflow past the bottom of the cell
                            if event_y_position > cell_bottom:
                                logger.warning(
                                    f"Event text overflowed in cell: {date_object}."
                                )
                                break  # Stop drawing events if the cell's bottom is reached
                else:
                    logger.debug(f"Skipping empty cell for day {day_of_month}.")
