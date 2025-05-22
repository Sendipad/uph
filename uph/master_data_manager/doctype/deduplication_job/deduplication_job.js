// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Deduplication Job", {
	document_type: (frm) => {
		// update the select field options with fieldnames
		if (frm.doc.document_type) {
			update_selection_fields(frm);
			frm.refresh_field("fields");
		}
	},
	refresh: function (frm) {
		update_selection_fields(frm);
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
function update_selection_fields(frm) {
	frappe.model.with_doctype(frm.doc.document_type, () => {
		const meta = frappe.get_meta(frm.doc.document_type);
		let options = [];

		// Add parent fields
		const parent_fields = meta.fields
			.filter((d) => frappe.model.no_value_type.indexOf(d.fieldtype) === -1)
			.map((d) => ({
				label: `${d.label} (${d.fieldname})`,
				value: d.fieldname,
			}));
		options = options.concat(parent_fields);

		// Add child table fields (grouped under parent field)
		const child_tables = meta.fields.filter((f) => f.fieldtype === "Table");
		child_tables.forEach((table_field) => {
			const child_meta = frappe.get_meta(table_field.options);
			child_meta.fields
				.filter((d) => frappe.model.no_value_type.indexOf(d.fieldtype) === -1)
				.forEach((d) => {
					options.push({
						label: `${table_field.label} → ${d.label} (${table_field.fieldname}.${d.fieldname})`,
						value: `${table_field.fieldname}.${d.fieldname}`, // Custom format
					});
				});
		});

		// Update options in child table
		frm.fields_dict.fields.grid.update_docfield_property("fieldname", "options", options);
	});
}
