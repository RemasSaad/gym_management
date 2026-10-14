
import frappe
from unittest.mock import patch
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, add_months, getdate, today


class TestGymMembership(FrappeTestCase):
    def test_end_date_for_day_plan(self):
        membership = frappe.new_doc("Gym Membership")
        membership.start_date = today()
        membership.membership_plan = "TEST-PLAN"

        plan = frappe._dict(
            duration_type="Days",
            duration_value=30,
            classes_included=0,
        )

        with patch.object(frappe.db, "get_value", return_value=plan):
            membership.validate_membership_plan()

        self.assertEqual(
            getdate(membership.end_date),
            getdate(add_days(today(), 29)),
        )

    def test_end_date_for_month_plan(self):
        membership = frappe.new_doc("Gym Membership")
        membership.start_date = today()
        membership.membership_plan = "TEST-PLAN"

        plan = frappe._dict(
            duration_type="Months",
            duration_value=3,
            classes_included=0,
        )

        with patch.object(frappe.db, "get_value", return_value=plan):
            membership.validate_membership_plan()

        self.assertEqual(
            getdate(membership.end_date),
            getdate(add_months(today(), 3)),
        )

    def test_class_pack_sets_classes_remaining(self):
        membership = frappe.new_doc("Gym Membership")
        membership.start_date = today()
        membership.membership_plan = "TEST-PLAN"

        plan = frappe._dict(
            duration_type="Class Pack",
            duration_value=1,
            classes_included=12,
        )

        with patch.object(frappe.db, "get_value", return_value=plan):
            membership.validate_membership_plan()

        self.assertEqual(membership.classes_remaining, 12)

    def test_end_date_before_start_date_is_rejected(self):
        membership = frappe.new_doc("Gym Membership")
        membership.start_date = add_days(today(), 5)
        membership.end_date = today()

        with self.assertRaises(frappe.ValidationError):
            membership.validate_dates()

    def test_existing_invoice_prevents_duplicate_creation(self):
        membership = frappe.new_doc("Gym Membership")
        membership.sales_invoice = "SINV-TEST-001"

        with patch.object(frappe, "get_doc") as get_doc:
            membership.on_submit()

        get_doc.assert_not_called()

    def test_missing_customer_is_rejected(self):
        membership = frappe.new_doc("Gym Membership")
        membership.member = "TEST-MEMBER"
        membership.membership_plan = "TEST-PLAN"

        with patch.object(
            frappe.db, "get_value", return_value=None
        ), patch.object(frappe, "get_doc") as get_doc:
            with self.assertRaises(frappe.ValidationError):
                membership.on_submit()

        get_doc.assert_not_called()

    def test_missing_plan_item_is_rejected(self):
        membership = frappe.new_doc("Gym Membership")
        membership.member = "TEST-MEMBER"
        membership.membership_plan = "TEST-PLAN"

        member_data = frappe._dict(customer="TEST-CUSTOMER")
        plan_data = frappe._dict(item=None, price=500, plan_name="Monthly")

        with patch.object(
            frappe.db, "get_value", side_effect=[member_data, plan_data]
        ), patch.object(frappe, "get_doc") as get_doc:
            with self.assertRaises(frappe.ValidationError):
                membership.on_submit()

        get_doc.assert_not_called()



class TestMembershipFreeze(FrappeTestCase):
    def _make_membership(self, freeze_history=None):
        membership = frappe._dict(
            name="TEST-MEMBERSHIP",
            docstatus=1,
            status="Active",
            membership_plan="TEST-PLAN",
            end_date=add_days(today(), 20),
            freeze_history=freeze_history or [],
            flags=frappe._dict(),
        )
        membership.append = lambda field, row: membership[field].append(
            frappe._dict(row)
        )
        membership.save = lambda **kwargs: None
        membership.db_set = lambda field, value, **kwargs: setattr(
            membership, field, value
        )
        return membership

    @patch(
        "gym_management.gym_management.doctype.gym_membership.gym_membership.frappe.get_doc"
    )
    @patch(
        "gym_management.gym_management.doctype.gym_membership.gym_membership.frappe.db.get_value"
    )
    def test_freeze_success_extends_end_date(self, get_value, get_doc):
        from gym_management.gym_management.doctype.gym_membership.gym_membership import (
            freeze_membership,
        )

        membership = self._make_membership()
        original_end = getdate(membership.end_date)
        get_doc.return_value = membership
        get_value.return_value = frappe._dict(max_freeze_days=10)

        result = freeze_membership(
            "TEST-MEMBERSHIP", today(), add_days(today(), 2), "Vacation"
        )

        self.assertEqual(result["days"], 3)
        self.assertEqual(
            getdate(membership.end_date), add_days(original_end, 3)
        )
        self.assertEqual(membership.status, "Frozen")
        self.assertEqual(len(membership.freeze_history), 1)

    @patch(
        "gym_management.gym_management.doctype.gym_membership.gym_membership.frappe.get_doc"
    )
    def test_freeze_rejects_non_active_membership(self, get_doc):
        from gym_management.gym_management.doctype.gym_membership.gym_membership import (
            freeze_membership,
        )

        membership = self._make_membership()
        membership.status = "Expired"
        get_doc.return_value = membership

        with self.assertRaises(frappe.ValidationError):
            freeze_membership("TEST-MEMBERSHIP", today(), today())

    @patch(
        "gym_management.gym_management.doctype.gym_membership.gym_membership.frappe.get_doc"
    )
    def test_freeze_rejects_invalid_date_range(self, get_doc):
        from gym_management.gym_management.doctype.gym_membership.gym_membership import (
            freeze_membership,
        )

        get_doc.return_value = self._make_membership()

        with self.assertRaises(frappe.ValidationError):
            freeze_membership(
                "TEST-MEMBERSHIP", add_days(today(), 2), today()
            )

    @patch(
        "gym_management.gym_management.doctype.gym_membership.gym_membership.frappe.get_doc"
    )
    @patch(
        "gym_management.gym_management.doctype.gym_membership.gym_membership.frappe.db.get_value"
    )
    def test_freeze_rejects_plan_without_freeze_days(self, get_value, get_doc):
        from gym_management.gym_management.doctype.gym_membership.gym_membership import (
            freeze_membership,
        )

        get_doc.return_value = self._make_membership()
        get_value.return_value = frappe._dict(max_freeze_days=0)

        with self.assertRaises(frappe.ValidationError):
            freeze_membership("TEST-MEMBERSHIP", today(), today())

    @patch(
        "gym_management.gym_management.doctype.gym_membership.gym_membership.frappe.get_doc"
    )
    @patch(
        "gym_management.gym_management.doctype.gym_membership.gym_membership.frappe.db.get_value"
    )
    def test_freeze_rejects_exceeding_plan_limit(self, get_value, get_doc):
        from gym_management.gym_management.doctype.gym_membership.gym_membership import (
            freeze_membership,
        )

        history = [frappe._dict(days=4)]
        get_doc.return_value = self._make_membership(history)
        get_value.return_value = frappe._dict(max_freeze_days=5)

        with self.assertRaises(frappe.ValidationError):
            freeze_membership(
                "TEST-MEMBERSHIP", today(), add_days(today(), 1)
            )
