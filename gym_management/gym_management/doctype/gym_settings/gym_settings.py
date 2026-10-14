
import frappe
from frappe.model.document import Document


class GymSettings(Document):
    def validate(self):
        self.validate_cancellation_window()
        self.validate_expiry_reminder()

    def validate_cancellation_window(self):
        if self.cancellation_window_hours is not None:
            if self.cancellation_window_hours < 0:
                frappe.throw("Cancellation Window cannot be negative.")

    def validate_expiry_reminder(self):
        if self.expiry_reminder_days is not None:
            if self.expiry_reminder_days < 0:
                frappe.throw("Expiry Reminder Days cannot be negative.")
