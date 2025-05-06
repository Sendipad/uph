// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt

frappe.query_reports["Chronological Party Ledger"] = {
	"filters": [
		{
			fieldname: "party_name",
			fieldtype: "Data",
			hidden: 1,
			label: __("Party Name"),
			default: "",
		  },
		  {
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		  },
		  {
			fieldname: "party_master",
			label: __("Party"),
			fieldtype: "Link",
			reqd: 1,
			options: "Party Master",
			get_data: function () {
				return frappe.db.get_link_options("Party Master", txt, {
					is_group: ["!=",1],
				});
			},
			on_change: function () {
				const party_master = frappe.query_report.get_filter_value("party_master");
		
				if (!party_master) {
					frappe.query_report.set_filter_value("party_name", "");
					return;
				}
		
				frappe.db.get_value("Party Master", party_master, "party_name", (r) => {
					if (r && r.party_name) {
						frappe.query_report.set_filter_value("party_name", r.party_name);
					}
				});
			}
		},		
		{
		  fieldname: "from_date",
		  label: __("Start Date"),
		  fieldtype: "Date",
		  default: frappe.datetime.add_months(frappe.datetime.get_today(), -12),
		  reqd: 1,
		},
	
		{
		  fieldname: "to_date",
		  label: __("End Date"),
		  fieldtype: "Date",
		  default: frappe.datetime.get_today(),
		  reqd: 1,
		},
	],
	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
	
		if (data && data.color) {
			value = `<span style='background-color:${data.color}; font-weight:bold'>` + value.bold() + `</span>`;
		}
	
		return value;
	}
};
