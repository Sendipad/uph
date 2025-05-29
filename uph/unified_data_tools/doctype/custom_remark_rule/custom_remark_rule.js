// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt
frappe.ui.form.on("Custom Remark Rule", {
	onload(frm) {
		frm.trigger("setup_field_options");
	},
	setup_field_options(frm) {
		if (frm.doc.document_type) {
			uph.utils.FieldOptionHelper.load({
				documentType: frm.doc.document_type,
				callback(options) {
					uph.utils.FieldOptionHelper.applyAutocomplete(
						frm,
						options,
						["remark_fieldname"], // parent fields
					);
					uph.utils.FieldOptionHelper.applyAutocomplete(
						frm,
						options,
						["fieldname"],
						"conditions", // parent fields
					);
				},
			});
		}
	},
	refresh(frm) {
		/* if (frm.doc.document_type) {
			const options = uph.utils.FieldOptionHelper.cache[frm.doc.document_type];
			if (options) {
				uph.utils.FieldOptionHelper.applyAutocomplete({
					frm,
					options,
					fieldnames: ["remark_fieldname"],
				});
			}
		} */
	},

	document_type: function (frm) {
		frm.trigger("setup_field_options");
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
