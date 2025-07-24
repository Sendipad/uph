// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rule Service Type", {
	onload(frm) {
		if (!frm.is_new()) {
			frm.disable_form();
		}
	},
});
