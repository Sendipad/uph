frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Party Identity Governance"] = {
	method: "uph.party.dashboard_chart_source.party_identity_governance.party_identity_governance.get_data",
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
	],
};
