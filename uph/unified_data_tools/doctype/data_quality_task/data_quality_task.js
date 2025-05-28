// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Data Quality Task", {
	onload: function (frm) {
		frm.set_read_only();
	},
	refresh: function (frm) {
		frm.set_read_only();

		if (frm.doc.resolved !== 1) {
			frm.add_custom_button(__("Mark as Resolved"), async function () {
				frm.set_value("resolved", 1);
				await frm.save();
				frm.reload_doc(); // reload triggers onload, which sets readonly
			});
		}
	},
});
