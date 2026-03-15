frappe.query_reports["Unlinked Parties"] = {
	filters: [
		{
			fieldname: "role_doctype",
			label: __("Role DocType"),
			fieldtype: "Link",
			options: "DocType",
			reqd: 0,
			get_query: function () {
				return {
					filters: {
						name: ["in", ["Customer", "Supplier", "Employee"]],
					},
				};
			},
		},
	],
};
