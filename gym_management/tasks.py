import frappe
from frappe.utils import add_days, getdate, today


def update_membership_statuses():
    """Expire memberships and restore memberships after their freeze ends."""

    current_date = getdate(today())

    memberships = frappe.get_all(
        "Gym Membership",
        filters={
            "docstatus": 1,
            "status": ["in", ["Active", "Frozen"]],
        },
        fields=["name", "status", "end_date"],
    )

    for membership in memberships:
        # Check whether this membership has a recorded freeze period.
        if membership.status == "Frozen":
            freeze_periods = frappe.get_all(
                "Membership Freeze",
                filters={
                    "parent": membership.name,
                    "parenttype": "Gym Membership",
                    "parentfield": "freeze_history",
                },
                fields=["freeze_from", "freeze_to"],
                order_by="idx desc",
                limit=1,
            )

            # Do not change the status if the freeze history is missing.
            if not freeze_periods:
                continue

            freeze_to = freeze_periods[0].freeze_to

            # The freeze is still in progress.
            if getdate(freeze_to) >= current_date:
                continue

            # The freeze ended. Restore Active only if the membership
            # itself has not expired.
            if membership.end_date and getdate(
                membership.end_date
            ) >= current_date:
                frappe.db.set_value(
                    "Gym Membership",
                    membership.name,
                    "status",
                    "Active",
                    update_modified=False,
                )
            else:
                frappe.db.set_value(
                    "Gym Membership",
                    membership.name,
                    "status",
                    "Expired",
                    update_modified=False,
                )

        elif membership.status == "Active":
            if (
                membership.end_date
                and getdate(membership.end_date) < current_date
            ):
                frappe.db.set_value(
                    "Gym Membership",
                    membership.name,
                    "status",
                    "Expired",
                    update_modified=False,
                )


def send_membership_expiry_reminders():
    """Email members whose active memberships expire soon."""

    settings = frappe.get_single("Gym Settings")
    reminder_days = settings.expiry_reminder_days or 7
    target_date = add_days(today(), reminder_days)

    memberships = frappe.get_all(
        "Gym Membership",
        filters={
            "docstatus": 1,
            "status": "Active",
            "end_date": target_date,
        },
        fields=["name", "member", "end_date"],
    )

    for membership in memberships:
        email = frappe.db.get_value(
            "Gym Member",
            membership.member,
            "email",
        )

        if not email:
            continue

        frappe.sendmail(
            recipients=[email],
            subject="Your gym membership is expiring soon",
            message=(
                f"Your gym membership {membership.name} "
                f"expires on {membership.end_date}. "
                "Please contact the gym to renew it."
            ),
            now=True,
        )