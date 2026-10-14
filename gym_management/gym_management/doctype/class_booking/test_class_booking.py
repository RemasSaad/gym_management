import frappe
from unittest.mock import patch
from frappe.tests.utils import FrappeTestCase


class TestClassBooking(FrappeTestCase):
    def test_missing_session_is_rejected(self):
        booking = frappe.new_doc("Class Booking")
        booking.class_session = "INVALID-SESSION"

        with patch.object(frappe.db, "get_value", return_value=None):
            with self.assertRaises(frappe.ValidationError):
                booking.validate_session()

    def test_missing_member_is_rejected(self):
        booking = frappe.new_doc("Class Booking")
        booking.member = "INVALID-MEMBER"

        with patch.object(frappe.db, "exists", return_value=False):
            with self.assertRaises(frappe.ValidationError):
                booking.validate_member()

    def test_duplicate_booking_is_rejected(self):
        booking = frappe.new_doc("Class Booking")
        booking.class_session = "TEST-SESSION"
        booking.member = "TEST-MEMBER"

        with patch.object(
            frappe.db, "exists", return_value="EXISTING-BOOKING"
        ):
            with self.assertRaises(frappe.ValidationError):
                booking.validate_duplicate_booking()

    def test_available_capacity_assigns_booked_status(self):
        booking = frappe.new_doc("Class Booking")
        booking.class_session = "TEST-SESSION"
        booking._session = frappe._dict(capacity=1)

        with patch.object(frappe.db, "count", return_value=0):
            booking.assign_booking_status()

        self.assertEqual(booking.status, "Booked")

    def test_full_session_assigns_waitlisted_status(self):
        booking = frappe.new_doc("Class Booking")
        booking.class_session = "TEST-SESSION"
        booking._session = frappe._dict(capacity=1)

        with patch.object(frappe.db, "count", return_value=1):
            with patch.object(
                frappe, "get_single",
                return_value=frappe._dict(enable_waitlist=1),
            ):
                booking.assign_booking_status()

        self.assertEqual(booking.status, "Waitlisted")

    def test_full_session_rejected_when_waitlist_disabled(self):
        booking = frappe.new_doc("Class Booking")
        booking.class_session = "TEST-SESSION"
        booking._session = frappe._dict(capacity=1)

        with patch.object(frappe.db, "count", return_value=1):
            with patch.object(
                frappe, "get_single",
                return_value=frappe._dict(enable_waitlist=0),
            ):
                with self.assertRaises(frappe.ValidationError):
                    booking.assign_booking_status()
