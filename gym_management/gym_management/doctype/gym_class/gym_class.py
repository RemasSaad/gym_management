
import frappe
from frappe.model.document import Document


class GymClass(Document):
    def validate(self):
        self.validate_duration()
        self.validate_capacity()
        self.validate_trainer()
        self.validate_room()

    def validate_duration(self):
        if not self.duration_minutes or self.duration_minutes <= 0:
            frappe.throw("Duration must be greater than zero.")

    def validate_capacity(self):
        if not self.default_capacity or self.default_capacity <= 0:
            frappe.throw("Default Capacity must be greater than zero.")

    def validate_trainer(self):
        if self.default_trainer:
            active = frappe.db.get_value(
                "Gym Trainer", self.default_trainer, "is_active"
            )
            if not active:
                frappe.throw("The selected trainer is inactive.")

    def validate_room(self):
        if self.default_room:
            active = frappe.db.get_value(
                "Gym Room", self.default_room, "is_active"
            )
            if not active:
                frappe.throw("The selected room is inactive.")
