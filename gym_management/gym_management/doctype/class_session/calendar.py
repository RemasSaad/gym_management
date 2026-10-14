import frappe
from frappe.utils import get_datetime


@frappe.whitelist()
def get_class_session_events(start, end, filters=None, **kwargs):
    sessions = frappe.get_all(
        "Class Session",
        filters=[
            ["Class Session", "session_date", ">=", start[:10]],
            ["Class Session", "session_date", "<=", end[:10]],
            ["Class Session", "status", "!=", "Cancelled"],
        ],
        fields=[
            "name",
            "gym_class",
            "session_date",
            "start_time",
            "end_time",
        ],
        order_by="session_date asc, start_time asc",
    )

    events = []
    for session in sessions:
        class_name = frappe.db.get_value(
            "Gym Class", session.gym_class, "class_name"
        ) or session.gym_class

        start_dt = get_datetime(
            f"{session.session_date} {session.start_time}"
        )
        end_dt = get_datetime(
            f"{session.session_date} {session.end_time or session.start_time}"
        )

        events.append({
            "name": session.name,
            "title": class_name,
            "start": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "end": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "allDay": False,
        })

    return events
