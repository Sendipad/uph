/*frappe.ui.form.on("Sales Invoice", {
    setup: function(frm) {
        uph.party.setups(frm);
        uph.party.set_party_query(frm);
        
    },
    party_master: function(frm) {
        uph.party.handle_party_master_change(frm);
    },
    refresh:function(frm){
        if (frm.doc.party_master){
            uph.party.set_party_query(frm);
        }
    },
    customer: function(frm) {
        uph.party.on_party_field_change(frm);
        uph.party.check_duplicate_party_master(frm);
    },
    posting_date:function(frm) {
        uph.party.check_duplicate_party_master(frm);

    },
    before_submit:function(frm){
        uph.party.check_duplicate_party_master(frm,true);

    }
});*/