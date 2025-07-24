// Form Event Handlers
frappe.ui.form.on("Rule", {
	onload: function (frm) {
		frm.controller = new uph.hub.RuleController(frm);
	},

	refresh: function (frm) {
		if (frm.controller) {
			frm.controller.apply_ui_customizations();
		}
	},

	rule_service_type: function (frm) {
		if (frm.controller) {
			frm.controller.apply_ui_customizations();
		}
	},
});
