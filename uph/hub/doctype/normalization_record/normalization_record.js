// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Normalization Record", {
	// 	refresh(frm) {

	// 	},
	docname(frm) {
		frm.events.reset_original_data(frm);
		frm.events.reset_normalized_date(frm);
	},
	reset_original_data(frm) {
		if (frm.doc.original_data) {
			frm.set_value("original_data");
			frm.refresh_field("original_data");
		}
	},
	reset_normalized_date(frm) {
		if (frm.doc.normalized_data) {
			frm.set_value("normalized_data");
			frm.refresh_field("normalized_data");
		}
	},
	normalization_profile(frm) {
		frm.events.reset_normalized_date(frm);
	},
	field_path(frm) {
		frm.events.reset_original_data(frm);
		frm.events.reset_normalized_date(frm);
	},
});
