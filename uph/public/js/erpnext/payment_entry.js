frappe.ui.form.on("Payment Entry", {
	setup(frm) {
		if (window.uph?.party) {
			if (!frm._uph_party_setup_done) {
				frm._uph_party_setup_done = true;
				uph.party.setups(frm);
			}
			uph.party.set_party_query(frm, "party");
		}
	},
	onload(frm) {
		if (window.uph?.party) {
			uph.party.set_party_query(frm, "party");
		}
	},
	refresh(frm) {
		if (window.uph?.party) {
			uph.party.refresh(frm);
			uph.party.set_party_query(frm, "party");
		}
	},
	party_master(frm) {
		if (window.uph?.party) {
			uph.party.handle_party_master_change(frm, "party");
		}
	},
	party_type(frm) {
		if (frm.uph_setting_party_master) return;
		if (window.uph?.party) {
			frm.set_value("party_master", "");
			uph.party.set_party_query(frm, "party");
		}
	},
	party(frm) {
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
