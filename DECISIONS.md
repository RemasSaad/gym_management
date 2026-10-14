# Design Decisions — Gym Management System

## R1. Subscription vs. Custom Billing

I used custom billing logic to create an ERPNext Sales Invoice when a Gym Membership is submitted. The invoice is linked to the membership, and it is cancelled when the membership is cancelled.

This approach provides direct control over the gym membership lifecycle and invoice creation. ERPNext Subscription is more suitable for recurring billing schedules and automated renewals, but it introduces additional configuration and lifecycle considerations. If automatic recurring payments and renewals become a core requirement, ERPNext Subscription should be evaluated.

## R2. Trainer Modeling

I modeled trainers using a separate `Gym Trainer` DocType rather than adding gym-specific fields to ERPNext Employee.

This keeps gym-specific information separate from general HR data and allows the gym to manage trainer specialties and availability independently. If integration with HR becomes necessary, a Gym Trainer can be linked to an Employee.

## R3. Pro-rated Refunds

For a membership cancelled before its end date, the system should calculate the unused service value according to the gym's refund policy.

The refund should be processed through ERPNext accounting using the appropriate credit note or return Sales Invoice workflow, subject to accounting permissions and company configuration. The calculation should consider the membership price, consumed period or classes, applicable fees, and refund policy. Refunds should require authorization and must not silently delete or modify submitted accounting records.

## R4. Concurrent Class Booking

To prevent two users from booking the last available spot simultaneously, capacity validation must be performed inside a database transaction with appropriate locking.

The booking process should lock the relevant Class Session record, recalculate confirmed bookings, and then create a booking or waitlist entry. The transaction should commit only after validation succeeds. Duplicate bookings should be prevented with server-side validation, and retries should be handled safely.

## R5. References

- Frappe Framework documentation: https://docs.frappe.io/framework
- ERPNext documentation: https://docs.erpnext.com
- Frappe DocType controllers and document lifecycle hooks.
- Frappe whitelisted methods and REST API conventions.
- ERPNext Sales Invoice and accounting workflows.

## Assumptions

- The application targets Frappe Framework v15 and ERPNext v15.
- Gym Membership billing uses custom logic integrated with ERPNext Sales Invoices.
- Refund handling is a design proposal and is not claimed to be implemented.
- Concurrency protection must be verified against the actual booking implementation before production use.
