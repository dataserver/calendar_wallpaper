import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from tkcalendar import DateEntry
from ttkthemes import ThemedTk

from config.config import Config
from models.common import publish_calendar_image
from utils.logger import setup_logger

logger = setup_logger(name="gui_logger")


# ---------- GUI Class ----------
# class Gui(tk.Tk):
class Gui(ThemedTk):
    def __init__(self, config):
        # super().__init__()
        super().__init__(theme="breeze")
        self.cfg = config
        self.title("📅 Calendar Event Manager")
        self.geometry("750x500")
        self.resizable(False, False)
        self.configure(padx=20, pady=20)

        logger.info("CalendarApp initialized.")
        self.create_widgets()
        self.load_events()

    # ---------- Database Setup ----------
    def init_db(self):
        with sqlite3.connect(self.cfg.EVENTS_DB_FILE) as conn:
            c = conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    event_datetime TEXT NOT NULL
                )
                """
            )
            conn.commit()
        logger.info(f"Database initialized with file {self.cfg.EVENTS_DB_FILE}")

    def create_widgets(self):
        # ----- Input Frame -----
        input_frame = ttk.LabelFrame(self, text="Add/Edit Event")
        input_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(input_frame, text="Title:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        self.title_entry = ttk.Entry(input_frame, width=40)
        self.title_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(input_frame, text="Date:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        self.date_entry = DateEntry(input_frame, date_pattern="yyyy-mm-dd")
        self.date_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(input_frame, text="Time:").grid(
            row=2, column=0, padx=5, pady=5, sticky="e"
        )
        self.hour_var = tk.StringVar(value="12")
        self.minute_var = tk.StringVar(value="00")

        self.hour_box = ttk.Combobox(
            input_frame,
            textvariable=self.hour_var,
            width=5,
            values=[f"{i:02}" for i in range(24)],
        )
        self.minute_box = ttk.Combobox(
            input_frame,
            textvariable=self.minute_var,
            width=5,
            values=[f"{i:02}" for i in range(0, 60, 5)],
        )
        self.hour_box.grid(row=2, column=1, sticky="w", padx=(5, 0), pady=5)
        self.minute_box.grid(row=2, column=1, sticky="w", padx=(60, 0), pady=5)

        full_day_btn = ttk.Button(
            input_frame, text="🕛 Full Day Event", command=self.set_full_day
        )
        full_day_btn.grid(row=2, column=1, sticky="w", padx=(120, 0), pady=5)

        # Buttons
        button_frame = tk.Frame(input_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        self.add_button = ttk.Button(
            button_frame, text="➕ Add Event", command=self.add_event
        )
        self.add_button.pack(side="left", padx=5)

        self.update_button = ttk.Button(
            button_frame, text="✏️ Update Event", command=self.update_event
        )
        self.update_button.pack(side="left", padx=5)

        self.delete_button = ttk.Button(
            button_frame, text="🗑️ Delete Event", command=self.delete_event
        )
        self.delete_button.pack(side="left", padx=5)

        self.clear_button = ttk.Button(
            button_frame, text="❌ Clear", command=self.clear_inputs
        )
        self.clear_button.pack(side="left", padx=5)

        self.publish_button = ttk.Button(
            button_frame,
            text="🖼️ Publish Calendar Image",
            command=self.publish_calendar,
        )
        self.publish_button.pack(side="left", padx=5)

        # ----- Event List -----
        list_frame = ttk.LabelFrame(self, text="📋 Event List")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("id", "datetime", "title")
        self.tree = ttk.Treeview(
            list_frame, columns=columns, show="headings", selectmode="browse", height=10
        )
        self.tree.heading("id", text="ID")
        self.tree.heading("datetime", text="Date & Time")
        self.tree.heading("title", text="Title")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("datetime", width=150)
        self.tree.column("title", width=500)

        self.tree.bind("<<TreeviewSelect>>", self.on_event_select)

        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        # Refresh Button
        refresh_frame = tk.Frame(self)
        refresh_frame.pack()
        ttk.Button(refresh_frame, text="🔄 Refresh", command=self.load_events).pack(
            pady=5
        )
        logger.debug("Widgets created.")

    def get_datetime_str(self):
        date = self.date_entry.get()
        hour = self.hour_var.get()
        minute = self.minute_var.get()
        datetime_str = f"{date} {hour}:{minute}"
        logger.debug(f"Generated datetime string: {datetime_str}")
        return datetime_str

    def load_events(self):
        self.tree.delete(*self.tree.get_children())
        with sqlite3.connect(self.cfg.EVENTS_DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, event_datetime, title FROM events ORDER BY event_datetime ASC"
            )
            rows = cursor.fetchall()
            logger.debug(f"database {self.cfg.EVENTS_DB_FILE}")
            logger.info(f"Loaded {len(rows)} events from database.")

            for row in rows:
                self.tree.insert("", "end", values=row)

    def add_event(self):
        title = self.title_entry.get().strip()
        datetime_str = self.get_datetime_str()

        if not title:
            logger.warning("Event title is required.")
            messagebox.showwarning("Input Error", "Event title is required.")
            return

        if not self.validate_datetime(datetime_str):
            logger.error(f"Invalid datetime format: {datetime_str}")
            messagebox.showerror("Invalid Date", "Date and time format is incorrect.")
            return

        with sqlite3.connect(self.cfg.EVENTS_DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO events (title, event_datetime) VALUES (?, ?)",
                (title, datetime_str),
            )
            conn.commit()

        logger.info(f"Added event: {title} at {datetime_str}")
        self.clear_inputs()
        self.load_events()

    def update_event(self):
        selected = self.tree.selection()
        if not selected:
            logger.info("No event selected to update.")
            messagebox.showinfo("No Selection", "Please select an event to update.")
            return

        item = self.tree.item(selected[0])
        event_id = item["values"][0]
        title = self.title_entry.get().strip()
        datetime_str = self.get_datetime_str()

        if not title:
            logger.warning("Event title is required for update.")
            messagebox.showwarning("Input Error", "Event title is required.")
            return

        if not self.validate_datetime(datetime_str):
            logger.error(f"Invalid datetime format for update: {datetime_str}")
            messagebox.showerror("Invalid Date", "Date and time format is incorrect.")
            return

        with sqlite3.connect(self.cfg.EVENTS_DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE events SET title = ?, event_datetime = ? WHERE id = ?",
                (title, datetime_str, event_id),
            )
            conn.commit()

        logger.info(
            f"Updated event ID {event_id} with title: {title} at {datetime_str}"
        )
        self.clear_inputs()
        self.load_events()

    def delete_event(self):
        selected = self.tree.selection()
        if not selected:
            logger.info("No event selected to delete.")
            messagebox.showinfo("No Selection", "Please select an event to delete.")
            return

        item = self.tree.item(selected[0])
        event_id = item["values"][0]

        confirm = messagebox.askyesno(
            "Confirm Delete", "Are you sure you want to delete this event?"
        )
        if confirm:
            with sqlite3.connect(self.cfg.EVENTS_DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
                conn.commit()
            logger.info(f"Deleted event ID {event_id}")

        self.clear_inputs()
        self.load_events()

    def on_event_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        event_id, datetime_str, title = item["values"]

        # Populate fields
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, title)

        try:
            dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            self.date_entry.set_date(dt.date())
            self.hour_var.set(f"{dt.hour:02}")
            self.minute_var.set(f"{dt.minute:02}")
            logger.debug(f"Event selected: {title} at {datetime_str}")
        except Exception as e:
            logger.error(f"Error parsing datetime for event: {datetime_str} - {e}")

    def clear_inputs(self):
        self.title_entry.delete(0, tk.END)
        self.date_entry.set_date(datetime.now().date())
        self.hour_var.set("12")
        self.minute_var.set("00")
        self.tree.selection_remove(self.tree.selection())
        logger.debug("Cleared input fields.")

    def validate_datetime(self, dt_str):
        try:
            datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            return True
        except ValueError:
            return False

    def publish_calendar(self):
        try:
            publish_calendar_image(
                year=datetime.today().year,
                month=datetime.today().month,
                start_of_week="sun",
                update_wallpaper=True,
            )
            logger.info("Calendar image generated and set as wallpaper.")
            messagebox.showinfo(
                "Success", "Calendar image generated and set as wallpaper."
            )
        except Exception as e:
            logger.error(f"Failed to generate calendar image: {e}")
            messagebox.showerror("Error", f"Failed to generate calendar:\n{e}")

    def set_full_day(self):
        self.hour_var.set("00")
        self.minute_var.set("00")
        logger.debug("Set event to full day.")


# ---------- Main ----------
if __name__ == "__main__":
    config = Config()
    app = Gui(config)
    app.mainloop()
