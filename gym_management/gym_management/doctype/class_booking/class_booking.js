frappe.ui.form.on("Class Booking", {
    setup(frm) {
        frm.set_query("class_session", () => ({
            filters: [
                ["Class Session", "status", "=", "Scheduled"],
                ["Class Session", "session_date", ">=", frappe.datetime.get_today()]
            ]
        }));
    },

    refresh(frm) {
        if (frm.doc.class_session) {
            frappe.db.get_value(
                "Class Session",
                frm.doc.class_session,
                ["capacity", "booked_count", "status"]
            ).then(r => {
                if (r.message) {
                    const available = Math.max(
                        0,
                        (r.message.capacity || 0) - (r.message.booked_count || 0)
                    );

                    frm.dashboard.set_headline(
                        __("Session status: {0} | Available spots: {1}", [
                            r.message.status,
                            available
                        ])
                    );
                }
            });
        }
    }
});
