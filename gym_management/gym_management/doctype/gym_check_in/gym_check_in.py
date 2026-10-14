
import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today


class GymCheckIn(Document):
    def validate(self):
        self.validate_member()
        self.validate_membership()
        self.validate_duplicate_check_in()

    def validate_duplicate_check_in(self):
        """Prevent a member from checking in more than once per day."""
        current_date = getdate(today())

        duplicate = frappe.db.sql(
            """
            SELECT name
            FROM `tabGym Check In`
            WHERE member = %s
              AND DATE(check_in_time) = %s
              AND name != %s
            LIMIT 1
            """,
            (self.member, current_date, self.name or ""),
        )

        if duplicate:
            frappe.throw(
                "This member has already checked in today."
            )

    def validate_member(self):
        if not self.member or not frappe.db.exists("Gym Member", self.member):
            frappe.throw("A valid Gym Member is required.")

    def validate_membership(self):
        membership_name = self.membership

        if not membership_name:
            membership_name = frappe.db.get_value(
                "Gym Member",
                self.member,
                "active_membership",
            )

        if not membership_name:
            frappe.throw("This member has no linked active membership.")

        membership = frappe.db.get_value(
            "Gym Membership",
            membership_name,
            ["member", "status", "start_date", "end_date"],
            as_dict=True,
        )

        if not membership or membership.member != self.member:
            frappe.throw("The selected membership does not belong to this member.")

        if membership.status != "Active":
            frappe.throw("Check-in requires an active membership.")

        current_date = getdate(today())

        if membership.start_date and current_date < getdate(membership.start_date):
            frappe.throw("The membership has not started yet.")

        if membership.end_date and current_date > getdate(membership.end_date):
            frappe.throw("The membership has expired.")

        self.membership = membership_name
