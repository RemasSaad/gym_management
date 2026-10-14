
import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today, now_datetime


ACTIVE_BOOKING_STATUSES = ["Booked", "Attended"]


class ClassBooking(Document):
    def validate(self):
        self.validate_session()
        self.validate_member()
        self.set_active_membership()
        self.validate_membership()
        self.validate_duplicate_booking()
        self.assign_booking_status()

    def validate_session(self):
        if not self.class_session:
            frappe.throw("Class Session is required.")

        # Lock this session row before checking capacity.
        # Concurrent booking transactions for the same session must wait
        # for the lock holder to finish before counting confirmed bookings.
        rows = frappe.db.sql(
            """
            SELECT status, capacity, session_date
            FROM `tabClass Session`
            WHERE name = %s
            FOR UPDATE
            """,
            (self.class_session,),
            as_dict=True,
        )
        session = rows[0] if rows else None

        if not session:
            frappe.throw("Selected class session does not exist.")

        if session.status != "Scheduled":
            frappe.throw("Only scheduled sessions can be booked.")

        if getdate(session.session_date) < getdate(today()):
            frappe.throw("Past sessions cannot be booked.")

        self._session = session

    def validate_member(self):
        if not self.member or not frappe.db.exists(
            "Gym Member", self.member
        ):
            frappe.throw("A valid Gym Member is required.")

    def set_active_membership(self):
        membership = frappe.db.get_value(
            "Gym Membership",
            {
                "member": self.member,
                "status": "Active",
                "docstatus": 1,
            },
            ["name", "start_date", "end_date"],
            as_dict=True,
        )

        if not membership:
            frappe.throw(
                "This member has no active submitted membership."
            )

        session_date = getdate(self._session.session_date)

        if membership.start_date and session_date < getdate(
            membership.start_date
        ):
            frappe.throw("Membership is not active on the session date.")

        if membership.end_date and session_date > getdate(
            membership.end_date
        ):
            frappe.throw("Membership has expired for the session date.")

        self.membership = membership.name

    def validate_membership(self):
        membership = frappe.db.get_value(
            "Gym Membership",
            self.membership,
            ["member", "status", "start_date", "end_date", "docstatus"],
            as_dict=True,
        )

        if (
            not membership
            or membership.member != self.member
            or membership.status != "Active"
            or membership.docstatus != 1
        ):
            frappe.throw("A valid active membership is required.")

        session_date = getdate(self._session.session_date)

        if membership.start_date and session_date < getdate(
            membership.start_date
        ):
            frappe.throw("Membership has not started for this session.")

        if membership.end_date and session_date > getdate(
            membership.end_date
        ):
            frappe.throw("Membership has expired for this session.")

    def validate_duplicate_booking(self):
        filters = {
            "class_session": self.class_session,
            "member": self.member,
            "status": [
                "in",
                ["Booked", "Waitlisted", "Attended"],
            ],
        }

        if self.name:
            filters["name"] = ["!=", self.name]

        if frappe.db.exists("Class Booking", filters):
            frappe.throw(
                "This member already has a booking for this session."
            )

    def assign_booking_status(self):
        if not self.is_new():
            return

        capacity = self._session.capacity or 0
        booked_count = frappe.db.count(
            "Class Booking",
            filters={
                "class_session": self.class_session,
                "status": ["in", ACTIVE_BOOKING_STATUSES],
            },
        )

        if booked_count < capacity:
            self.status = "Booked"
            return

        settings = frappe.get_single("Gym Settings")

        if settings.enable_waitlist:
            self.status = "Waitlisted"
        else:
            frappe.throw(
                "This session is full and the waitlist is disabled."
            )

    def on_update(self):
        self.refresh_session_count()

        if self.status == "Cancelled":
            if not self.cancelled_on:
                self.db_set(
                    "cancelled_on",
                    now_datetime(),
                    update_modified=False,
                )

            self.promote_waitlist()

    def on_trash(self):
        self.refresh_session_count()

    def refresh_session_count(self):
        if not self.class_session:
            return

        count = frappe.db.count(
            "Class Booking",
            filters={
                "class_session": self.class_session,
                "status": ["in", ACTIVE_BOOKING_STATUSES],
            },
        )

        frappe.db.set_value(
            "Class Session",
            self.class_session,
            "booked_count",
            count,
            update_modified=False,
        )

    def promote_waitlist(self):
        session = frappe.db.get_value(
            "Class Session",
            self.class_session,
            ["status", "capacity"],
            as_dict=True,
        )

        if not session or session.status != "Scheduled":
            return

        booked_count = frappe.db.count(
            "Class Booking",
            filters={
                "class_session": self.class_session,
                "status": ["in", ACTIVE_BOOKING_STATUSES],
            },
        )

        if booked_count >= (session.capacity or 0):
            return

        next_booking = frappe.get_all(
            "Class Booking",
            filters={
                "class_session": self.class_session,
                "status": "Waitlisted",
            },
            fields=["name", "member"],
            order_by="booked_on asc",
            limit=1,
        )

        if not next_booking:
            return

        booking = frappe.get_doc(
            "Class Booking", next_booking[0].name
        )
        booking.status = "Booked"
        booking.save(ignore_permissions=True)

        member_email = frappe.db.get_value(
            "Gym Member", booking.member, "email"
        )

        if member_email:
            frappe.sendmail(
                recipients=[member_email],
                subject="Gym class booking confirmed",
                message=(
                    f"Your booking for session "
                    f"{self.class_session} is now confirmed."
                ),
                now=True,
            )
            
            
@frappe.whitelist()
def refresh_all_session_counts():
    sessions = frappe.get_all(
        "Class Session",
        filters={"name": ["is", "set"]},
        pluck="name",
    )

    for session_name in sessions:
        count = frappe.db.count(
            "Class Booking",
            filters={
                "class_session": session_name,
                "status": ["in", ["Booked", "Attended"]],
            },
        )

        frappe.db.set_value(
            "Class Session",
            session_name,
            "booked_count",
            count,
            update_modified=False,
        )

    frappe.db.commit()
    return f"Updated booking counts for {len(sessions)} sessions."

