import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today


class TestClassSession(FrappeTestCase):
    def test_zero_capacity_is_rejected(self):
        session = frappe.new_doc("Class Session")
        session.capacity = 0

        with self.assertRaises(frappe.ValidationError):
            session.validate_capacity()

    def test_end_time_uses_class_duration(self):
        gym_class = frappe.get_doc({
            "doctype": "Gym Class",
            "class_name": "Test Yoga Session",
            "duration_minutes": 45,
            "default_capacity": 10,
        }).insert(ignore_permissions=True)

        self.addCleanup(
            frappe.delete_doc,
            "Gym Class",
            gym_class.name,
            force=True,
        )

        session = frappe.new_doc("Class Session")
        session.gym_class = gym_class.name
        session.session_date = add_days(today(), 1)
        session.start_time = "10:00:00"

        session.set_end_time()

        self.assertEqual(str(session.end_time), "10:45:00")
