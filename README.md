# Gym Management System

A Gym Management application built with Frappe Framework v15 and ERPNext v15.

The application manages gym members, membership plans, memberships, class sessions, class bookings, trainers, rooms, and check-ins. It integrates membership billing with ERPNext Sales Invoices.

## Requirements

- Frappe Framework v15
- ERPNext v15
- A working Frappe Bench environment

## Installation

Run the following commands from your bench directory:

```bash
bench get-app gym_management <REPOSITORY_URL>
bench --site <SITE_NAME> install-app gym_management
bench --site <SITE_NAME> migrate
bench --site <SITE_NAME> clear-cache
```

Replace `<REPOSITORY_URL>` with the Git repository URL and `<SITE_NAME>` with your Frappe site name.

If the app is already available under `apps/gym_management`, skip `bench get-app`.

## Main Features

- Gym member management with automatic Customer creation.
- Membership plans linked to ERPNext Items.
- Membership lifecycle management and end-date calculation.
- Sales Invoice creation when a membership is submitted, with cancellation of the linked invoice when the membership is cancelled.
- Class sessions, bookings, capacity validation, and waitlist handling.
- Membership check-in validation.
- Membership expiry reminders and scheduled status updates.
- Membership Expiry Report.
- Automated tests for core membership, booking, and class-session behavior.

## Running Tests

Run the tests from the bench directory:

```bash
bench --site <SITE_NAME> run-tests --module gym_management.gym_management.doctype.class_booking.test_class_booking
bench --site <SITE_NAME> run-tests --module gym_management.gym_management.doctype.gym_membership.test_gym_membership
bench --site <SITE_NAME> run-tests --module gym_management.gym_management.doctype.class_session.test_class_session
```

The three test modules above have been executed successfully in the development environment.

## Implementation Notes

- The app uses ERPNext Customers, Items, and Sales Invoices for its relevant business records.
- Membership billing uses custom logic to create a Sales Invoice when a membership is submitted.
- The app is designed to run as a separate Frappe application without modifying Frappe or ERPNext core files.

## License

MIT
