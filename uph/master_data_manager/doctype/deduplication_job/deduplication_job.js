// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Deduplication Job", {
	document_type: (frm) => {
		// update the select field options with fieldnames
		if (frm.doc.document_type) {
			frappe.model.with_doctype(frm.doc.document_type, () => {
				let fieldnames = frappe
					.get_meta(frm.doc.document_type)
					.fields.filter((d) => {
						return frappe.model.no_value_type.indexOf(d.fieldtype) === -1;
					})
					.map((d) => {
						return { label: `${d.label} (${d.fieldname})`, value: d.fieldname };
					});
				frm.fields_dict.fields.grid.update_docfield_property("fieldname", "options", fieldnames);
			});
		}
	},
	refresh: function (frm) {
		if (!frm.doc.__islocal) {
			frm.add_custom_button("Run Now", function () {
				frappe.call({
					method: "run_job",
					doc: frm.doc,
					callback: function (r) {
						frappe.msgprint(__("Deduplication run complete."));
					},
				});
			});
		}
	},
});
