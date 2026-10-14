
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


@frappe.whitelist()
def search_front_desk_members(query):
    """Search members and resolve their current valid membership."""
    query = (query or "").strip()
    if len(query) < 2:
        return []

    pattern = f"%{query}%"
    members = frappe.db.sql(
        """
        SELECT name, member_name, phone, active_membership
        FROM `tabGym Member`
        WHERE member_name LIKE %(pattern)s
           OR phone LIKE %(pattern)s
        ORDER BY member_name
        LIMIT 20
        """,
        {"pattern": pattern},
        as_dict=True,
    )

    current_date = today()

    for member in members:
        membership = frappe.db.get_value(
            "Gym Membership",
            {
                "member": member.name,
                "docstatus": 1,
                "status": "Active",
                "start_date": ["<=", current_date],
            },
            ["name", "status", "start_date", "end_date"],
            as_dict=True,
            order_by="start_date desc",
        )

        if membership and membership.end_date and getdate(membership.end_date) < getdate(current_date):
            membership = None

        member["membership"] = membership.name if membership else None
        member["membership_status"] = "Active" if membership else "No active membership"

        if membership and member.active_membership != membership.name:
            frappe.db.set_value(
                "Gym Member",
                member.name,
                "active_membership",
                membership.name,
                update_modified=False,
            )

    return members

@frappe.whitelist()
def get_gym_dashboard_stats():
    """Return live statistics for the Gym Management dashboard."""
    from frappe.utils import add_days, get_first_day, get_last_day, today

    current_date = today()
    next_week = add_days(current_date, 7)
    month_start = get_first_day(current_date)
    month_end = get_last_day(current_date)

    active_members = frappe.db.count(
        "Gym Membership",
        filters={"docstatus": 1, "status": "Active"},
    )

    expiring_memberships = frappe.db.count(
        "Gym Membership",
        filters={
            "docstatus": 1,
            "status": "Active",
            "end_date": ["between", [current_date, next_week]],
        },
    )

    sessions = frappe.db.sql(
        """
        SELECT COALESCE(SUM(capacity), 0) AS total_capacity,
               COALESCE(SUM(booked_count), 0) AS total_booked
        FROM `tabClass Session`
        WHERE session_date = %(current_date)s
          AND status != 'Cancelled'
        """,
        {"current_date": current_date},
        as_dict=True,
    )[0]

    capacity = sessions.total_capacity or 0
    booked = sessions.total_booked or 0
    fill_rate = round((booked / capacity) * 100, 2) if capacity else 0

    revenue = frappe.db.sql(
        """
        SELECT COALESCE(SUM(grand_total), 0)
        FROM `tabSales Invoice`
        WHERE docstatus = 1
          AND status != 'Return'
          AND posting_date BETWEEN %(month_start)s AND %(month_end)s
        """,
        {"month_start": month_start, "month_end": month_end},
    )[0][0] or 0

    return {
        "active_members": active_members,
        "expiring_in_7_days": expiring_memberships,
        "today_fill_rate": fill_rate,
        "today_booked": booked,
        "today_capacity": capacity,
        "revenue_this_month": revenue,
    }
