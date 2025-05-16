// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt

frappe.query_reports["Party Master Health Report"] = {
	filters: [
		{
			label: __("Match Exist Party Master on Voucher To Party"),
			fieldname: "match_exists_party_master_on_voucher_to_party",
			fieldtype: "Check",
			default: 1,
		},
		{
			label: __("Party Master"),
			fieldtype: "Link",
			fieldname: "party_master",
			options: "Party Master",
		},
	],
};
