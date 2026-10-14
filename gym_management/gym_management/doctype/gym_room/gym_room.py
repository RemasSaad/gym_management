
import frappe
from frappe.model.document import Document


class GymRoom(Document):
    def validate(self):
        if not self.room_name or not self.room_name.strip():
            frappe.throw("Room Name is required.")

        if not self.capacity or self.capacity <= 0:
            frappe.throw("Room capacity must be greater than zero.")
