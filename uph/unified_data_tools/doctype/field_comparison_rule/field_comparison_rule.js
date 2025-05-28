// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Field Comparison Rule", {
	onload(frm) {
		if (frm.doc.document_type) {
			uph.utils.FieldOptionHelper.load({
				documentType: frm.doc.document_type,
				callback(options) {
					uph.utils.FieldOptionHelper.applyAutocomplete(
						frm,
						options,
						["fieldname", "with_field"], // parent fields
					);
				},
			});
		}
	},
	document_type(frm) {
		if (!frm.doc.document_type) return;

		uph.utils.FieldOptionHelper.load({
			documentType: frm.doc.document_type,
			callback(options) {
				uph.utils.FieldOptionHelper.applyAutocomplete(
					frm,
					options,
					["fieldname", "with_field"], // parent fields
				);
			},
		});
	},

	refresh(frm) {
		if (frm.doc.document_type) {
			const options = uph.utils.FieldOptionHelper.cache[frm.doc.document_type];
			if (options) {
				uph.utils.FieldOptionHelper.applyAutocomplete({
					frm,
					options,
					fieldnames: ["fieldname", "with_field"],
				});
			}
		}
	},
});
