// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt
frappe.ui.form.on("Field Comparison Job", {
	rules: function (frm) {
		frm.fields_dict.rules.get_query = function () {
			return {
				filters: {
					document_type: frm.doc.document_type,
				},
			};
		};
	},

	document_type: function (frm) {
		frm.fields_dict.rules.get_query = function () {
			return {
				filters: {
					document_type: frm.doc.document_type,
				},
			};
		};
	},

	refresh: function (frm) {
		if (frm.doc.status !== "Running" || frm.doc.status !== "Queued") {
			frm.add_custom_button(
				__("Run Job Now"),
				function () {
					frappe.call({
						method: "uph.unified_data_tools.api.field_comparison_job.run_job",
						args: {
							job_name: frm.doc.name,
						},
						callback: function (r) {
							if (!r.exc) {
								frappe.msgprint(__("Field Comparison Job executed successfully."));
								frm.reload_doc();
							}
						},
					});
				},
				__("Actions"),
			);
		}
	},
});
