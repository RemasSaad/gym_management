
import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime


class ClassSession(Document):
    def validate(self):
        self.set_end_time()
        self.validate_capacity()
        self.validate_room_capacity()
        self.validate_schedule_conflicts()
        self.update_booked_count()

    def set_end_time(self):
        if not self.gym_class or not self.session_date or not self.start_time:
            return

        duration = frappe.db.get_value(
            "Gym Class", self.gym_class, "duration_minutes"
        )

        if not duration or duration <= 0:
            frappe.throw("The class duration must be greater than zero.")

        start = get_datetime(f"{self.session_date} {self.start_time}")
        end = start + __import__("datetime").timedelta(minutes=duration)
        self.end_time = end.strftime("%H:%M:%S")

    def validate_capacity(self):
        if not self.capacity or self.capacity <= 0:
            frappe.throw("Capacity must be greater than zero.")

    def validate_room_capacity(self):
        if not self.room or not self.capacity:
            return

        room_capacity = frappe.db.get_value(
            "Gym Room", self.room, "capacity"
        )

        if room_capacity and self.capacity > room_capacity:
            frappe.throw(
                f"Session capacity cannot exceed room capacity ({room_capacity})."
            )

    def update_booked_count(self):
        if not self.name or self.is_new():
            self.booked_count = 0
            return

        self.booked_count = frappe.db.count(
            "Class Booking",
            filters={
                "class_session": self.name,
                "status": ["in", ["Booked", "Attended"]],
            },
        )

    def validate_schedule_conflicts(self):
        if not all([
            self.session_date,
            self.start_time,
            self.end_time,
            self.trainer,
            self.room,
        ]):
            return

        sessions = frappe.get_all(
            "Class Session",
            filters={
                "session_date": self.session_date,
                "status": "Scheduled",
                "name": ["!=", self.name or ""],
            },
            fields=[
                "name", "start_time", "end_time", "trainer", "room"
            ],
        )

        for session in sessions:
            overlaps = (
                str(self.start_time) < str(session.end_time)
                and str(self.end_time) > str(session.start_time)
            )

            if not overlaps:
                continue

            if session.trainer == self.trainer:
                frappe.throw(
                    f"Trainer already has an overlapping session: {session.name}"
                )

            if session.room == self.room:
                frappe.throw(
                    f"Room already has an overlapping session: {session.name}"
                )
