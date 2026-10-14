
import frappe
from frappe.model.document import Document


class GymTrainer(Document):
    def validate(self):
        self.validate_trainer_name()
        self.validate_employee()

    def validate_trainer_name(self):
        if not self.trainer_name or not self.trainer_name.strip():
            frappe.throw("Trainer Name is required.")

    def validate_employee(self):
        if not self.employee:
            frappe.throw("An Employee must be linked to the trainer.")

        if not frappe.db.exists("Employee", self.employee):
            frappe.throw("The selected Employee does not exist.")
