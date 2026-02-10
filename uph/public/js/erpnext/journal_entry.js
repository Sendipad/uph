frappe.ui.form.on("Journal Entry", {
});

frappe.ui.form.on("Journal Entry Account", {
    party_type: function (frm, cdt, cdn) {
        if (frm.uph_setting_party_master) return;

        frappe.model.set_value(cdt, cdn, 'party_master', '');
        frm.refresh_field('accounts');
    }
});
