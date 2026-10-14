frappe.ui.form.on("Gym Membership", {
    refresh(frm) {
        if (frm.is_new() || frm.doc.docstatus !== 1) return;

        if (frm.doc.status === "Active") {
            frm.add_custom_button(__("Freeze"), () => {
                const today = frappe.datetime.get_today();

                const dialog = new frappe.ui.Dialog({
                    title: __("Freeze Membership"),
                    fields: [{
                            fieldname: "freeze_from",
                            label: __("Freeze From"),
                            fieldtype: "Date",
                            default: today,
                            reqd: 1
                        },
                        {
                            fieldname: "freeze_to",
                            label: __("Freeze To"),
                            fieldtype: "Date",
                            reqd: 1
                        },
                        {
                            fieldname: "reason",
                            label: __("Reason"),
                            fieldtype: "Small Text"
                        }
                    ],
                    primary_action_label: __("Confirm Freeze"),
                    primary_action(values) {
                        frappe.call({
                            method: "gym_management.gym_management.doctype.gym_membership.gym_membership.freeze_membership",
                            args: {
                                membership_name: frm.doc.name,
                                freeze_from: values.freeze_from,
                                freeze_to: values.freeze_to,
                                reason: values.reason || ""
                            },
                            freeze: true,
                            freeze_message: __("Freezing membership..."),
                            callback(r) {
                                if (r.message) {
                                    frappe.show_alert({
                                        message: r.message.message,
                                        indicator: "green"
                                    });
                                    dialog.hide();
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                });

                dialog.show();
            });
        }

        if (["Active", "Expired"].includes(frm.doc.status)) {
            frm.add_custom_button(__("Renew"), () => {
                frappe.confirm(
                    __("Create a new membership and invoice for this member?"),
                    () => {
                        frappe.call({
                            method: "gym_management.gym_management.doctype.gym_membership.gym_membership.renew_membership",
                            args: {
                                membership_name: frm.doc.name
                            },
                            freeze: true,
                            freeze_message: __("Creating renewal..."),
                            callback(r) {
                                if (r.message && r.message.membership) {
                                    frappe.show_alert({
                                        message: r.message.message,
                                        indicator: "green"
                                    });

                                    frappe.set_route(
                                        "Form",
                                        "Gym Membership",
                                        r.message.membership
                                    );
                                }
                            }
                        });
                    }
                );
            });
        }
    }
});