
import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, getdate


class MembershipFreeze(Document):
    def validate(self):
        self.validate_dates()
        self.calculate_days()

    def validate_dates(self):
        if not self.freeze_from or not self.freeze_to:
            frappe.throw("Both freeze dates are required.")

        if getdate(self.freeze_to) < getdate(self.freeze_from):
            frappe.throw("Freeze To cannot be before Freeze From.")

    def calculate_days(self):
        self.days = date_diff(self.freeze_to, self.freeze_from) + 1

