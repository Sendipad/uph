// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt

frappe.query_reports["Party Account Balances"] = {
	filters: [
		
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
			fieldtype: "MultiSelectList",
			options: "Party Master",
			get_data: (txt) => {
			  let group = frappe.query_report.get_filter_value("is_group");
			  return frappe.db.get_link_options("Party Master", txt, {
				is_group: group,
			  });
			},
			on_change: function () {
			  let parties = frappe.query_report.get_filter_value("party_master") || [];
			  
			  if (parties.length === 0) {
				frappe.query_report.set_filter_value("party_name", "");
			  } else {
				frappe.db.get_value('Party Master', parties[0], 'party_name', (value) => {
				  if (value && value.party_name) {
					frappe.query_report.set_filter_value("party_name", value.party_name);
				  }
				});
			  }
			},
		  },
		  
	
	
		{
		  fieldname: "to_date",
		  label: __("End Date"),
		  fieldtype: "Date",
		  default: frappe.datetime.get_today(),
		  reqd: 1,
		},
			
		
		
	
		{
		  fieldname: "group_by",
		  label: __("Group by"),
		  fieldtype: "Select",
		  options: [
			"",
			{
			  label: __("Default ordering"),
			  description: __("Party Master --> Party & Party Type->Posting Date"),
			  value: "Default",
			},
			{
			  label: __("Group by Voucher (Consolidated)"),
			  value: "Group by Voucher (Consolidated)",
			},
			{
			  label: __("Group by Account"),
			  value: "Group by Account",
			},
			{
			  label: __("Group by Party"),
			  value: "Group by Party",
			},
		  ],
		  default: "Group by Voucher (Consolidated)",
		},
	
		{
		  fieldname: "party_analytic_accounting",
		  label: __("Party Analytic Accounting"),
		  fieldtype: "MultiSelectList",
		  options: "Party Analytic Accounting",
		  get_data: function (txt) {
			if (frappe.query_report.get_filter_value("is_group")) return [];
			let party_master = frappe.query_report.get_filter_value("party_master");
			if (party_master.lenght > 1 || !party_master) return [];
			return frappe.db.get_link_options("Party Analytic Accounting", txt, {
			  party_master: party_master[0],
			});
		  },
		},
		{
		  fieldname: "cost_center",
		  label: __("Cost Center"),
		  fieldtype: "MultiSelectList",
		  options: "Cost Center",
		  get_data: function (txt) {
			return frappe.db.get_link_options("Cost Center", txt, {
			  company: frappe.query_report.get_filter_value("company"),
			});
		  },
		},
		{
		  fieldname: "project",
		  label: __("Project"),
		  fieldtype: "MultiSelectList",
		  options: "Project",
		  get_data: function (txt) {
			return frappe.db.get_link_options("Project", txt, {
			  company: frappe.query_report.get_filter_value("company"),
			});
		  },
		},


		{
			fieldname: "party_account",
			label: __("Receivable Account"),
			fieldtype: "Link",
			options: "Account",
			get_query: () => {
				var company = frappe.query_report.get_filter_value("company");
				return {
					filters: {
						company: company,
						account_type: "Receivable",
						is_group: 0,
					},
				};
			},
		},
		{
		  fieldname: "party_type",
		  label: __("Party Type"),
		  fieldtype: "MultiSelectList",
		  options: [],
		  get_data: (txt) => {
			let default_option = [
			  {
				value: "All",
				label: __("All"),
				description: __(
				  "Default to show accounting entries for all Party Types under Party Master"
				),
			  },
			];
	
			let dynamic_options = Object.keys(
			  frappe.boot.party_account_types || {}
			).map((key) => ({
			  value: key,
			  label: __(key),
			  description: __("only accounting entries for {0} will be shown", [
				__(key),
			  ]),
			}));
	
			return default_option.concat(dynamic_options);
		  },
		},
		{
		  fieldname: "presentation_currency",
		  label: __("Currency"),
		  fieldtype: "MultiSelectList",
		  options: erpnext.get_presentation_currency_list().map((currency) => ({
			value: currency,
			description: "",
			label: currency === "" ? __("For All Currencies") : __(currency),
		  })),
		},
		{
		  fieldname: "is_group",
		  label: __("For Group"),
		  fieldtype: "Check",
		  default: 1,
	
		  on_change: function () {
			frappe.query_report.set_filter_value("party", []);
		  },
		},
		
		
		{
		  fieldname: "in_company_currency",
		  label: __("Add Columns In Company Currency"),
		  fieldtype: "Check",
		  default: 0,
		},
		{
			fieldname: "payment_terms_template",
			label: __("Payment Terms Template"),
			fieldtype: "Link",
			options: "Payment Terms Template",
		},
		{
			fieldname: "sales_partner",
			label: __("Sales Partner"),
			fieldtype: "Link",
			options: "Sales Partner",
		},
		{
			fieldname: "sales_person",
			label: __("Sales Person"),
			fieldtype: "Link",
			options: "Sales Person",
		},
		{
			fieldname: "territory",
			label: __("Territory"),
			fieldtype: "Link",
			options: "Territory",
		},
		{
			fieldname: "group_by_party",
			label: __("Group By Customer"),
			fieldtype: "Check",
		},
		{
			fieldname: "based_on_payment_terms",
			label: __("Based On Payment Terms"),
			fieldtype: "Check",
		},
		{
			fieldname: "show_future_payments",
			label: __("Show Future Payments"),
			fieldtype: "Check",
		},
		{
			fieldname: "show_delivery_notes",
			label: __("Show Linked Delivery Notes"),
			fieldtype: "Check",
		},
		{
			fieldname: "show_sales_person",
			label: __("Show Sales Person"),
			fieldtype: "Check",
		},
		{
			fieldname: "show_remarks",
			label: __("Show Remarks"),
			fieldtype: "Check",
		},
		{
			fieldname: "for_revaluation_journals",
			label: __("Revaluation Journals"),
			fieldtype: "Check",
		},
		

	  ],
	
	  "formatter": function(value, row, column, data, default_formatter) {
			value = default_formatter(value, row, column, data);
			if (column.fieldname == "voucher_subtype" && data && data.voucher_subtype) {
				value = __(value);
			}
			if (column.fieldname == "party_type" && data && data.party_type) {
				value = __(value);
			}
			if (data =={}) {
				value = "";
	
			}
			if (data && data.bold) {
				value = "<span style='font-size:bold'>" + value.bold() + "</span>";
	
			}
			if (data && data.is_opening==1){
				value = "<span style='color:blue'>" + value + "</span>";
			}
			if (data && data.ending){
				value = "<span style='color:red'>" + value + "</span>";
			}
			return value;
		},
		onload: function (report) {
			report.page.add_inner_button(__("Party Account Statement"), function () {
				var filters = report.get_values();
				frappe.set_route("query-report", "Party Account Statement", { company: filters.company });
			});
		},
	
	};
	
erpnext.utils.add_dimensions("Party Account Balances", 9);
	