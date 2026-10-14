frappe.views.calendar["Class Session"] = {
    field_map: {
        start: "start",
        end: "end",
        id: "name",
        title: "title",
        allDay: "allDay"
    },
    order_by: "start",
    get_events_method:
        "gym_management.gym_management.doctype.class_session.calendar.get_class_session_events"
};
