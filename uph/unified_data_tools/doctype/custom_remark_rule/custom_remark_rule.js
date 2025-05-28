// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt
frappe.ui.form.on("Custom Remark Rule", {
	refresh: function (frm) {
		update_selection_fields(frm);
		//frm.refresh_field("conditions");
	},
	document_type: function (frm) {
		if (frm.doc.document_type) {
			update_selection_fields(frm);
			frm.refresh_field("conditions");
		}
	},
});

function update_selection_fields(frm) {
	if (!frm.doc.document_type) return;

	frappe.model.with_doctype(frm.doc.document_type, () => {
		let meta = frappe.get_meta(frm.doc.document_type);

		let valid_fields = meta.fields.filter(
			(d) => frappe.model.no_value_type.indexOf(d.fieldtype) === -1,
		);

		let fieldnames = valid_fields.map((d) => ({
			label: `${d.label} (${d.fieldname})`,
			value: d.fieldname,
		}));

		// Set options for child table select field
		frm.fields_dict.conditions.grid.update_docfield_property("field", "options", fieldnames);

		// Auto-select remark field if not set
		if (!frm.doc.remark_fieldname) {
			let preferred_fields = ["remark", "remarks", "user_remarks"];
			let match = valid_fields.find((f) => preferred_fields.includes(f.fieldname.toLowerCase()));

			if (match) {
				frm.set_value("remark_fieldname", match.fieldname);
			}
		}
	});
}
