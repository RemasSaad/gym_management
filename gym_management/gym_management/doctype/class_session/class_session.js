frappe.views.calendar["Class Session"] = {
    field_map: {
        start: "session_date",
        end: "session_date",
        id: "name",
        title: "gym_class",
        allDay: "all_day"
    },
    order_by: "session_date",
    get_events_method: "frappe.desk.calendar.get_events"
};

frappe.ui.form.on("Class Session", {
    refresh(frm) {
        frm.add_custom_button(__("View Class Calendar"), () => {
            frappe.set_route("List", "Class Session", "Calendar");
        });
    }
});
