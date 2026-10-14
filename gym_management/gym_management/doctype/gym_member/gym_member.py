
import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today


class GymMember(Document):
    def validate(self):
        self.validate_date_of_birth()
        self.validate_member_name()

    def after_insert(self):
        self.create_customer_if_missing()

    def create_customer_if_missing(self):
        if self.customer:
            return

        customer_group = "Individual"
        territory = "Egypt"

        if not frappe.db.exists("Customer Group", customer_group):
            frappe.throw(
                f"Customer Group '{customer_group}' does not exist."
            )

        if not frappe.db.exists("Territory", territory):
            frappe.throw(
                f"Territory '{territory}' does not exist."
            )

        customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": self.member_name.strip(),
            "customer_type": "Individual",
            "customer_group": customer_group,
            "territory": territory,
        })

        customer.insert(ignore_permissions=True)

        self.db_set(
            "customer",
            customer.name,
            update_modified=False
        )

    def validate_date_of_birth(self):
        if (
            self.date_of_birth
            and getdate(self.date_of_birth) > getdate(today())
        ):
            frappe.throw("Date of Birth cannot be in the future.")

    def validate_member_name(self):
        if not self.member_name or not self.member_name.strip():
            frappe.throw("Member Name is required.")
