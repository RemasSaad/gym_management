
import frappe
from frappe.utils import getdate, today, get_datetime


@frappe.whitelist()
def get_available_sessions(date_from, date_to):
    """Return scheduled future sessions with available spots."""

    date_from = getdate(date_from)
    date_to = getdate(date_to)

    if date_to < date_from:
        frappe.throw("End date cannot be before start date.")

    sessions = frappe.get_all(
        "Class Session",
        filters={
            "session_date": ["between", [date_from, date_to]],
            "status": "Scheduled",
        },
        fields=[
            "name",
            "gym_class",
            "trainer",
            "room",
            "session_date",
            "start_time",
            "end_time",
            "capacity",
        ],
        order_by="session_date asc, start_time asc",
    )

    available = []

    for session in sessions:
        if getdate(session.session_date) < getdate(today()):
            continue

        booked_count = frappe.db.count(
            "Class Booking",
            filters={
                "class_session": session.name,
                "status": ["in", ["Booked", "Attended"]],
            },
        )

        session["booked_count"] = booked_count
        session["available_spots"] = max(
            0, (session.capacity or 0) - booked_count
        )

        available.append(session)

    return available


@frappe.whitelist()
def book_class(session, member):
    """Book a member into a class session."""

    if not frappe.has_permission("Class Booking", "create"):
        frappe.throw(
            "You do not have permission to create bookings.",
            frappe.PermissionError,
        )

    booking = frappe.get_doc({
        "doctype": "Class Booking",
        "class_session": session,
        "member": member,
    })

    booking.insert()
    return {
        "name": booking.name,
        "status": booking.status,
        "message": (
            "Booking created successfully."
            if booking.status == "Booked"
            else "Session is full. Member added to waitlist."
        ),
    }
