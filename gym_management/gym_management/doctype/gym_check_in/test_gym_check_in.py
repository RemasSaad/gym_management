import frappe
from unittest.mock import patch
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today


class TestGymCheckIn(FrappeTestCase):
    def test_missing_member_is_rejected(self):
        checkin = frappe.new_doc("Gym Check In")
        checkin.member = "INVALID-MEMBER"

        with patch.object(frappe.db, "exists", return_value=False):
            with self.assertRaises(frappe.ValidationError):
                checkin.validate_member()

    def test_duplicate_checkin_is_rejected(self):
        checkin = frappe.new_doc("Gym Check In")
        checkin.member = "TEST-MEMBER"

        with patch.object(
            frappe.db, "sql", return_value=[{"name": "EXISTING-CHECKIN"}]
        ):
            with self.assertRaises(frappe.ValidationError):
                checkin.validate_duplicate_check_in()

    def test_frozen_membership_is_rejected(self):
        checkin = frappe.new_doc("Gym Check In")
        checkin.member = "TEST-MEMBER"
        checkin.membership = "TEST-MEMBERSHIP"

        membership = frappe._dict(
            member="TEST-MEMBER",
            status="Frozen",
            start_date=today(),
            end_date=add_days(today(), 10),
        )

        with patch.object(
            frappe.db, "get_value", return_value=membership
        ):
            with self.assertRaises(frappe.ValidationError):
                checkin.validate_membership()

    def test_expired_membership_is_rejected(self):
        checkin = frappe.new_doc("Gym Check In")
        checkin.member = "TEST-MEMBER"
        checkin.membership = "TEST-MEMBERSHIP"

        membership = frappe._dict(
            member="TEST-MEMBER",
            status="Active",
            start_date=add_days(today(), -30),
            end_date=add_days(today(), -1),
        )

        with patch.object(
            frappe.db, "get_value", return_value=membership
        ):
            with self.assertRaises(frappe.ValidationError):
                checkin.validate_membership()

    def test_valid_active_membership_is_accepted(self):
        checkin = frappe.new_doc("Gym Check In")
        checkin.member = "TEST-MEMBER"
        checkin.membership = "TEST-MEMBERSHIP"

        membership = frappe._dict(
            member="TEST-MEMBER",
            status="Active",
            start_date=add_days(today(), -1),
            end_date=add_days(today(), 30),
        )

        with patch.object(
            frappe.db, "get_value", return_value=membership
        ):
            checkin.validate_membership()

        self.assertEqual(checkin.membership, "TEST-MEMBERSHIP")
