frappe.query_reports["Party Health"] = {
	filters: [
		{
			fieldname: "party_master",
			label: __("Party Master"),
			fieldtype: "Link",
			options: "Party Master",
			reqd: 0,
		},
	],
};
