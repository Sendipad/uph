/*frappe.ui.form.on("Payment Entry", {
    setup: function(frm) {
		frm.show_party_selection_dialog=true;
        uph.party.setups(frm);
    },
    party_master: function(frm) {
        uph.party.handle_party_master_change(frm);
    },
    party: function(frm) {
        uph.party.on_party_field_change(frm);
        uph.party.check_duplicate_party_master(frm);

    },
	party_type:function(frm){
		frm.set_value('party_master','');
		frm.refresh_field('party_master');
        //uph.party.check_duplicate_party_master(frm);
	},
    posting_date:function(frm){
        uph.party.check_duplicate_party_master(frm);

    }
    
});*/