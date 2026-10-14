import frappe
from frappe.utils import add_days, add_months, getdate, now_datetime, today


COMPANY = "Gym Management"
ITEM_CODE = "GYM-MEMBERSHIP-BASIC"

MEMBERS = [
    ("Mariam Hassan", "mariam.demo@example.com", "+201010000001", "Female"),
    ("Omar Ahmed", "omar.demo@example.com", "+201010000002", "Male"),
    ("Nour Mohamed", "nour.demo@example.com", "+201010000003", "Female"),
    ("Youssef Ali", "youssef.demo@example.com", "+201010000004", "Male"),
    ("Salma Ibrahim", "salma.demo@example.com", "+201010000005", "Female"),
    ("Adam Mahmoud", "adam.demo@example.com", "+201010000006", "Male"),
]

PLANS = [
    ("Demo Basic Monthly", "Months", 1, 500, 7, 0),
    ("Demo Premium Quarterly", "Months", 3, 1300, 14, 0),
    ("Demo Annual Fitness", "Months", 12, 4500, 21, 0),
    ("Demo 10-Class Pack", "Class Pack", 10, 1000, 0, 10),
]

CLASSES = [
    ("Morning Yoga", "Yoga", 60, 20,
     "Beginner-friendly yoga, flexibility and balance."),
    ("HIIT Burn", "HIIT", 45, 15,
     "High-intensity interval training."),
    ("Indoor Spin", "Spin", 45, 18,
     "Indoor cycling endurance session."),
    ("Strength Fundamentals", "Strength", 60, 16,
     "Full-body strength and resistance training."),
    ("Power Yoga", "Yoga", 60, 18,
     "Dynamic yoga and mobility."),
    ("Express HIIT", "HIIT", 30, 12,
     "Short high-intensity workout."),
]


def get_or_create(doctype, filters, values):
    name = frappe.db.get_value(doctype, filters, "name")
    if name:
        return name

    doc = frappe.get_doc({"doctype": doctype, **values})
    doc.insert(ignore_permissions=True)
    return doc.name


def execute():
    if not frappe.db.exists("Company", COMPANY):
        frappe.throw(f"Company '{COMPANY}' does not exist.")

    if not frappe.db.exists("Item", ITEM_CODE):
        frappe.throw(
            f"Item '{ITEM_CODE}' does not exist. "
            "Create the membership service Item before seeding."
        )

    company = frappe.db.get_value(
        "Company", COMPANY, ["default_income_account"], as_dict=True
    )
    if not company or not company.default_income_account:
        frappe.throw(
            f"Configure the default income account for {COMPANY} first."
        )

    # Trainers and their required Employee records.
    trainer_names = [
        ("Mina Adel", "Male", "Strength and HIIT"),
        ("Sara Mostafa", "Female", "Yoga and mobility"),
        ("Karim Samir", "Male", "Indoor cycling"),
    ]
    trainers = []

    for full_name, gender, specialty in trainer_names:
        employee_id = frappe.db.get_value(
            "Employee",
            {"employee_name": full_name, "company": COMPANY},
            "name",
        )

        if not employee_id:
            employee = frappe.get_doc({
                "doctype": "Employee",
                "first_name": full_name.split()[0],
                "middle_name": " ".join(full_name.split()[1:]),
                "gender": gender,
                "date_of_birth": "1995-01-01",
                "date_of_joining": today(),
                "status": "Active",
                "company": COMPANY,
            })
            employee.insert(ignore_permissions=True)
            employee_id = employee.name

        trainer_id = get_or_create(
            "Gym Trainer",
            {"trainer_name": full_name},
            {
                "trainer_name": full_name,
                "employee": employee_id,
                "is_active": 1,
                "bio": f"Fitness instructor specializing in {specialty}.",
            },
        )
        trainers.append(trainer_id)

    # Training rooms.
    room_specs = [
        ("Studio A", 20),
        ("Spin Room", 18),
        ("Strength Floor", 16),
    ]
    rooms = []
    for room_name, capacity in room_specs:
        rooms.append(get_or_create(
            "Gym Room",
            {"room_name": room_name},
            {
                "room_name": room_name,
                "capacity": capacity,
                "is_active": 1,
            },
        ))

    # Membership plans use the existing service Item.
    plans = {}
    for name, duration_type, duration_value, price, max_freeze, classes in PLANS:
        plans[name] = get_or_create(
            "Membership Plan",
            {"plan_name": name},
            {
                "plan_name": name,
                "item": ITEM_CODE,
                "duration_type": duration_type,
                "duration_value": duration_value,
                "price": price,
                "max_freeze_days": max_freeze,
                "classes_included": classes,
                "is_active": 1,
            },
        )

    # Real fitness class types supported by the DocType's Select options.
    classes = []
    for index, (name, category, duration, capacity, description) in enumerate(CLASSES):
        trainer_id = trainers[index % len(trainers)]
        room_id = rooms[index % len(rooms)]
        class_id = get_or_create(
            "Gym Class",
            {"class_name": name},
            {
                "class_name": name,
                "category": category,
                "default_trainer": trainer_id,
                "default_room": room_id,
                "duration_minutes": duration,
                "default_capacity": capacity,
                "description": description,
            },
        )
        classes.append((class_id, trainer_id, room_id, duration, capacity))

    # Members; Gym Member's controller creates a Customer if needed.
    members = []
    for full_name, email, phone, gender in MEMBERS:
        member_id = get_or_create(
            "Gym Member",
            {"member_name": full_name},
            {
                "member_name": full_name,
                "email": email,
                "phone": phone,
                "gender": gender,
                "joined_on": today(),
                "status": "Active",
            },
        )
        members.append(member_id)

    # Create submitted memberships only if a matching demo membership
    # does not already exist. Submission creates a Sales Invoice.
    membership_specs = [
        (0, "Demo Basic Monthly", -5),
        (1, "Demo Premium Quarterly", -20),
        (2, "Demo Annual Fitness", -60),
        (3, "Demo Basic Monthly", -2),
        (4, "Demo 10-Class Pack", -1),
        (5, "Demo Premium Quarterly", 0),
    ]
    memberships = {}

    for member_index, plan_name, start_offset in membership_specs:
        member_id = members[member_index]
        plan_id = plans[plan_name]
        existing = frappe.db.get_value(
            "Gym Membership",
            {
                "member": member_id,
                "membership_plan": plan_id,
                "docstatus": ["!=", 2],
            },
            "name",
        )

        if existing:
            memberships[member_id] = existing
            continue

        start_date = add_days(today(), start_offset)
        membership = frappe.get_doc({
            "doctype": "Gym Membership",
            "member": member_id,
            "membership_plan": plan_id,
            "start_date": start_date,
            "auto_renew": 0,
        })
        membership.insert(ignore_permissions=True)
        membership.submit()
        memberships[member_id] = membership.name

    # Create future sessions across the next seven days, avoiding duplicates.
    sessions = []
    time_slots = ["08:00:00", "10:00:00", "17:00:00", "19:00:00"]

    for day_offset in range(1, 8):
        session_date = add_days(today(), day_offset)
        for slot_index, start_time in enumerate(time_slots):
            class_id, trainer_id, room_id, duration, capacity = classes[
                (day_offset + slot_index) % len(classes)
            ]
            existing = frappe.db.get_value(
                "Class Session",
                {
                    "gym_class": class_id,
                    "session_date": session_date,
                    "start_time": start_time,
                },
                "name",
            )

            if existing:
                session_id = existing
            else:
                from datetime import datetime, timedelta
                start_dt = datetime.strptime(start_time, "%H:%M:%S")
                end_time = (start_dt + timedelta(minutes=duration)).strftime(
                    "%H:%M:%S"
                )
                session = frappe.get_doc({
                    "doctype": "Class Session",
                    "gym_class": class_id,
                    "trainer": trainer_id,
                    "room": room_id,
                    "session_date": session_date,
                    "start_time": start_time,
                    "end_time": end_time,
                    "capacity": min(
                        capacity,
                        frappe.db.get_value("Gym Room", room_id, "capacity") or capacity,
                    ),
                    "booked_count": 0,
                    "status": "Scheduled",
                })
                session.insert(ignore_permissions=True)
                session_id = session.name

            sessions.append(session_id)

    # Book the first few sessions for members with submitted memberships.
    created_bookings = 0
    for index, member_id in enumerate(members[:5]):
        session_id = sessions[index]
        membership_id = memberships.get(member_id)

        existing = frappe.db.exists(
            "Class Booking",
            {
                "class_session": session_id,
                "member": member_id,
                "status": ["!=", "Cancelled"],
            },
        )
        if existing:
            continue

        booking = frappe.get_doc({
            "doctype": "Class Booking",
            "class_session": session_id,
            "member": member_id,
            "membership": membership_id,
            "status": "Booked",
            "booked_on": now_datetime(),
        })
        booking.insert(ignore_permissions=True)
        created_bookings += 1

    frappe.db.commit()

    print("\n=== GYM DEMO DATA READY ===")
    print("Members:", len(members))
    print("Membership plans:", len(plans))
    print("Trainers:", len(trainers))
    print("Rooms:", len(rooms))
    print("Classes:", len(classes))
    print("Future sessions:", len(set(sessions)))
    print("New bookings:", created_bookings)
    print("Submitted memberships create Sales Invoices.")
    print("Review the created memberships and invoices before using this on real data.")
