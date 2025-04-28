frappe.ui.form.on("Journal Entry", {
});
frappe.ui.form.on("Journal Entry Account", {
    accounts_add: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        frm.fields_dict['accounts'].grid.get_field('party_master').get_query = function(frm, cdt, cdn) {
            return {
                query:"uph.party.utils.get_party_master_list",
                filters: {
                    doctype: frm.doc.doctype,
                    reference_doctype: frm.doc.doctype,
                    disabled: 0,
                    is_group: 0,
                    party_type: row.party_type
                }
            };
        };
    },

    party_master: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        uph.party.handle_party_master_change_in_child(frm, row);
    },

    party: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        uph.party.on_party_field_change_in_child(frm, row);
    },

    party_type: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, 'party_master', '');
        frm.refresh_field('accounts');
    }
});
