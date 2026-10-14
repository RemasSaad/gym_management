frappe.query_reports["Membership Expiry Report"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            reqd: 0
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            reqd: 0
        },
        {
            fieldname: "membership_plan",
            label: __("Membership Plan"),
            fieldtype: "Link",
            options: "Membership Plan"
        },
        {
            fieldname: "status",
            label: __("Status"),
            fieldtype: "Select",
            options: "\nDraft\nActive\nFrozen\nExpired\nCancelled"
        }
    ]
};
