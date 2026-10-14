import frappe
from frappe.model.document import Document
from frappe.utils import (
    add_days,
    add_months,
    getdate,
    today,
    flt,
    date_diff,
)


class GymMembership(Document):
    def validate(self):
        self.validate_dates()
        self.validate_membership_plan()

    def validate_dates(self):
        if self.start_date and self.end_date:
            if getdate(self.end_date) < getdate(self.start_date):
                frappe.throw("End Date cannot be before Start Date.")

    def validate_membership_plan(self):
        if not self.membership_plan:
            return

        plan = frappe.db.get_value(
            "Membership Plan",
            self.membership_plan,
            ["duration_type", "duration_value", "classes_included"],
            as_dict=True,
        )

        if not plan:
            frappe.throw("Please select a valid Membership Plan.")

        if not self.start_date or not plan.duration_value:
            return

        start = getdate(self.start_date)

        if plan.duration_type == "Days":
            self.end_date = add_days(start, plan.duration_value - 1)

        elif plan.duration_type == "Months":
            self.end_date = add_months(start, plan.duration_value)

        elif plan.duration_type == "Class Pack":
            self.classes_remaining = plan.classes_included

    def on_submit(self):
        # Activate the membership when submitted.
        self.db_set("status", "Active", update_modified=False)

        # Prevent duplicate invoice creation.
        if self.sales_invoice:
            return

        member = frappe.db.get_value(
            "Gym Member",
            self.member,
            ["customer"],
            as_dict=True,
        )

        if not member or not member.customer:
            frappe.throw(
                "Please link this Gym Member to a Customer before submitting."
            )

        plan = frappe.db.get_value(
            "Membership Plan",
            self.membership_plan,
            ["item", "price", "plan_name"],
            as_dict=True,
        )

        if not plan or not plan.item:
            frappe.throw(
                "Please select an Item in the Membership Plan before submitting."
            )

        if not frappe.db.exists("Item", plan.item):
            frappe.throw(
                "The Item linked to this Membership Plan does not exist."
            )

        company = "Gym Management"

        company_settings = frappe.db.get_value(
            "Company",
            company,
            ["default_income_account", "default_currency"],
            as_dict=True,
        )

        if not company_settings:
            frappe.throw(f"Company '{company}' does not exist.")

        if not company_settings.default_income_account:
            frappe.throw(
                f"Configure the default income account for {company}."
            )

        invoice = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": member.customer,
            "company": company,
            "currency": company_settings.default_currency,
            "items": [
                {
                    "item_code": plan.item,
                    "qty": 1,
                    "rate": flt(plan.price),
                    "income_account": company_settings.default_income_account,
                    "description": f"Gym Membership: {plan.plan_name}",
                }
            ],
        })

        invoice.insert(ignore_permissions=True)
        invoice.submit()

        self.db_set(
            "sales_invoice",
            invoice.name,
            update_modified=False,
        )

    def on_cancel(self):
        if self.sales_invoice:
            invoice_status = frappe.db.get_value(
                "Sales Invoice",
                self.sales_invoice,
                "docstatus",
            )

            if invoice_status == 1:
                invoice = frappe.get_doc(
                    "Sales Invoice", self.sales_invoice
                )
                invoice.cancel()

        self.db_set("status", "Cancelled", update_modified=False)


@frappe.whitelist()
def freeze_membership(membership_name, freeze_from, freeze_to, reason=""):
    """Freeze an active membership and record the freeze period."""

    membership = frappe.get_doc("Gym Membership", membership_name)

    if membership.docstatus != 1 or membership.status != "Active":
        frappe.throw("Only active submitted memberships can be frozen.")

    freeze_from = getdate(freeze_from)
    freeze_to = getdate(freeze_to)
    current_date = getdate(today())

    if freeze_to < freeze_from:
        frappe.throw("Freeze To cannot be before Freeze From.")

    if not (freeze_from <= current_date <= freeze_to):
        frappe.throw("The freeze period must include today's date.")

    plan = frappe.db.get_value(
        "Membership Plan",
        membership.membership_plan,
        ["max_freeze_days"],
        as_dict=True,
    )

    max_days = (plan.max_freeze_days or 0) if plan else 0
    requested_days = date_diff(freeze_to, freeze_from) + 1

    if max_days <= 0:
        frappe.throw("This membership plan does not allow freezing.")

    used_days = sum(
        row.days or 0 for row in (membership.freeze_history or [])
    )

    if used_days + requested_days > max_days:
        frappe.throw(
            f"Freeze limit exceeded. Maximum allowed: {max_days} days."
        )

    # Record the freeze in the parent child table.
    membership.append(
        "freeze_history",
        {
            "freeze_from": freeze_from,
            "freeze_to": freeze_to,
            "days": requested_days,
            "reason": reason,
        },
    )

    membership.flags.ignore_validate_update_after_submit = True
    membership.save(ignore_permissions=True)

    # Extend the membership end date by the freeze duration.
    new_end_date = add_days(
        getdate(membership.end_date), requested_days
    )

    membership.db_set("end_date", new_end_date, update_modified=False)
    membership.db_set("status", "Frozen", update_modified=False)

    return {
        "message": "Membership frozen successfully.",
        "membership": membership.name,
        "end_date": str(new_end_date),
        "days": requested_days,
    }


@frappe.whitelist()
def renew_membership(membership_name):
    """Create a draft renewal without submitting or invoicing it."""

    membership = frappe.get_doc("Gym Membership", membership_name)

    if membership.docstatus != 1:
        frappe.throw("Only submitted memberships can be renewed.")

    if membership.status in ("Cancelled", "Frozen"):
        frappe.throw(
            "Cancelled or frozen memberships cannot be renewed."
        )

    current_date = getdate(today())

    if (
        membership.end_date
        and getdate(membership.end_date) >= current_date
    ):
        new_start_date = add_days(
            getdate(membership.end_date), 1
        )
    else:
        new_start_date = current_date

    new_membership = frappe.get_doc({
        "doctype": "Gym Membership",
        "member": membership.member,
        "membership_plan": membership.membership_plan,
        "start_date": new_start_date,
        "auto_renew": membership.auto_renew,
    })

    # Save as Draft. on_submit will not run, so no invoice is created.
    new_membership.insert(ignore_permissions=True)

    return {
        "message": (
            "Draft renewal membership created successfully. "
            "No invoice was generated."
        ),
        "membership": new_membership.name,
        "start_date": str(new_start_date),
        "status": new_membership.status,
        "docstatus": new_membership.docstatus,
    }