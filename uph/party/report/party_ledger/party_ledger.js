// Copyright (c) 2025, Abdo Ruzaqi and contributors
// For license information, please see license.txt

frappe.query_reports["Party Ledger"] = {
	"filters": [
		{
			"fieldname":"party_name",
			"label": __("Accounts Name"),
			"fieldtype": "Data",
			"read_only": 1,
			"hidden": 1
		},
				
		{
			"fieldname": "for_group",
			"label": __("For Group"),
			"fieldtype": "Check",
			"default": 0
		},
		{
			"fieldname":"party",
			"label": __("Party Master"),
			"fieldtype": "MultiSelectList",
			"options":"Party Master",
			get_data: function(txt) {
				//let isgroup=frappe.query_report.get_filter_value('for_group');
				return frappe.db.get_link_options('Party Master', txt,
					{is_group:frappe.query_report.get_filter_value('for_group'),
					});
				},
			on_change: () => {
				frappe.db.get_value('Party Master', frappe.query_report.get_filter_value('party'), 'party_name', function(value) {
					frappe.query_report.set_filter_value('party_name', value["party_name"]);
				});
			}
		},
	
		
		{
			"fieldname":"from_date",
			"label": __("Start Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -4),
			"reqd": 1
		},

		{
			"fieldname":"to_date",
			"label": __("End Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		
		
		{
			"fieldname": "show_documents_summary",
			"label": __("Show Documents Summary"),
			"fieldtype": "Check",
			"default": 1,
		},
		
	
		
		{
			"fieldname": "all_currency",
			"label": __("All Currency"),
			"fieldtype": "Check",
			"default": 1
		},

		{
			"fieldname": "group_by_voucher_consolidate",
			"label": __("Group By Voucher Consolidate"),
			"fieldtype": "Check",
			"default": 1,
			
		},
		{
			"fieldname": "hide_equals_dr_cr_tx",
			"label": __("Hide Equals Voucher"),
			"fieldtype": "Check",
			"default": 0,
			"depends_on": 'eval:doc.group_by_voucher_consolidate',

		},
		{
			"fieldname": "ignore_err",
			"label": __("Hide Currency Exchange reconsolidation"),
			"fieldtype": "Check",
			"default": 1
		},
		
		{
			"fieldname": "presentation_currency",
			"label": __("Currency"),
			"fieldtype": "Select",
			"depends_on": 'eval:!doc.all_currency',
			"options": erpnext.get_presentation_currency_list()
		},
		{
			"fieldname": "include_dimensions",
			"label": __("Consider Accounting Dimensions"),
			"fieldtype": "Check",
			"default": 0
		},
		{
			"fieldname": "show_opening_entries",
			"label": __("Show Opening Entries"),
			"fieldtype": "Check",
			"default": 0
		},
		{
			"fieldname": "show_cancelled_entries",
			"label": __("Show Cancelled Entries"),
			"fieldtype": "Check",
			"default":0
		},
		{
			"fieldname":"cost_center",
			"label": __("Cost Center"),
			"fieldtype": "MultiSelectList",
			get_data: function(txt) {
				return frappe.db.get_link_options('Cost Center', txt, {
					company: frappe.query_report.get_filter_value("company")
				});
			}
		},
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname":"not_include_voucher_no",
			"label": __("Selected Voucher Not Include"),
			"hidden":1,
			"fieldtype": "Data",
			/* get_data: function(txt) {
				return frappe.db.get_link_options('Cost Center', txt, {
					company: frappe.query_report.get_filter_value("company")
				});
			} */
		},
	],
	onload: function (report) {

		var letter_heads=Object.keys(frappe.boot.letter_heads);
		/* function() {
			frappe.ui.get_print_settings(true, function(print_settings) {
				me.print_settings = print_settings;
				me.pdf_report();
			}, me.report_doc.letter_head);
		}, tr */
		frappe.ui.keys.add_shortcut({
			shortcut: "alt+ctrl+a",
			description: __("Download PDF"),
			action: () => {
				get_print_settings(true,(print_settings) => frappe.query_report.pdf_report(print_settings),letter_heads[0]);

			}
		});
		/*report.page.add_inner_button(__("Download PDF"), function() {
			// function here. Will Add only to Report View
			var print_settings = locals[":Print Settings"]["Print Settings"];
			print_settings.with_letter_head=1;
			print_settings.orientation="Portrait";
			print_settings.letter_head=letter_heads[0];
			console.log(print_settings);
			frappe.query_report.pdf_report(print_settings);
			get_print_settings(true,(print_settings) => frappe.query_report.pdf_report(print_settings),letter_heads[0]);

		});*/

       
		report.page.set_primary_action(__("Download PDF"), function() {
			// When this button is clicked, do this
			get_print_settings(true,(print_settings) => frappe.query_report.pdf_report(print_settings),letter_heads[0]);

		});
	
    },
}
erpnext.utils.add_dimensions('Party Ledger', 16);

