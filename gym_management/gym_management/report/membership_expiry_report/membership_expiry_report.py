import frappe
from frappe import _
from frappe.utils import getdate, today


def execute(filters=None):
    filters = frappe._dict(filters or {})
    validate_filters(filters)

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def validate_filters(filters):
    if filters.get("from_date") and filters.get("to_date"):
        if getdate(filters.from_date) > getdate(filters.to_date):
            frappe.throw(_("From Date cannot be after To Date."))


def get_columns():
    return [
        {
            "label": _("Membership"),
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Gym Membership",
            "width": 160,
        },
        {
            "label": _("Member"),
            "fieldname": "member",
            "fieldtype": "Link",
            "options": "Gym Member",
            "width": 160,
        },
        {
            "label": _("Plan"),
            "fieldname": "membership_plan",
            "fieldtype": "Link",
            "options": "Membership Plan",
            "width": 150,
        },
        {
            "label": _("Start Date"),
            "fieldname": "start_date",
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "label": _("End Date"),
            "fieldname": "end_date",
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": _("Days Remaining"),
            "fieldname": "days_remaining",
            "fieldtype": "Int",
            "width": 120,
        },
    ]


def get_data(filters):
    conditions = [
        "docstatus = 1",
        "end_date IS NOT NULL",
    ]
    values = {}

    if filters.get("from_date"):
        conditions.append("end_date >= %(from_date)s")
        values["from_date"] = filters.from_date

    if filters.get("to_date"):
        conditions.append("end_date <= %(to_date)s")
        values["to_date"] = filters.to_date

    if filters.get("membership_plan"):
        conditions.append("membership_plan = %(membership_plan)s")
        values["membership_plan"] = filters.membership_plan

    if filters.get("status"):
        conditions.append("status = %(status)s")
        values["status"] = filters.status

    memberships = frappe.db.sql(
        f"""
        SELECT name, member, membership_plan,
               start_date, end_date, status
        FROM `tabGym Membership`
        WHERE {" AND ".join(conditions)}
        ORDER BY end_date ASC
        """,
        values,
        as_dict=True,
    )

    current_date = getdate(today())

    for row in memberships:
        row["days_remaining"] = (
            getdate(row.end_date) - current_date
        ).days

    return memberships
