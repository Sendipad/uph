frappe.ui.form.on("Sales Invoice", {
	setup(frm) {
		if (window.uph?.party) {
			if (!frm._uph_party_setup_done) {
				frm._uph_party_setup_done = true;
				uph.party.setups(frm);
			}
			uph.party.set_party_query(frm, "customer");
		}
	},
	onload(frm) {
		if (window.uph?.party) {
			uph.party.set_party_query(frm, "customer");
		}
	},
	refresh(frm) {
		if (window.uph?.party) {
			uph.party.refresh(frm);
			uph.party.set_party_query(frm, "customer");
		}
	},
	party_master(frm) {
		if (window.uph?.party) {
			uph.party.handle_party_master_change(frm, "customer");
		}
	},
	customer(frm) {
		if (window.uph?.party) {
			uph.party.on_party_field_change(frm);
		}
	},
	posting_date(frm) {
		if (window.uph?.party) {
			uph.party.check_duplicate_voucher_for_party_master(frm);
		}
	},
});
