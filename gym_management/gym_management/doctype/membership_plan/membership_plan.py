
import frappe
from frappe.model.document import Document
from frappe.utils import flt


class MembershipPlan(Document):
    def validate(self):
        self.validate_duration()
        self.validate_price()
        self.validate_class_pack()

    def validate_duration(self):
        if not self.duration_value or self.duration_value <= 0:
            frappe.throw("Duration Value must be greater than zero.")

    def validate_price(self):
        if flt(self.price) < 0:
            frappe.throw("Price cannot be negative.")

    def validate_class_pack(self):
        if self.duration_type == "Class Pack":
            if not self.classes_included or self.classes_included <= 0:
                frappe.throw(
                    "Classes Included must be greater than zero for Class Pack plans."
                )
