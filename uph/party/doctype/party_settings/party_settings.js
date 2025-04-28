frappe.ui.form.on("Party Settings", {
    refresh: function(frm) {
        frm.refresh_field('document_type');
        if (frm.doc.document_type && frm.doc.document_type.length) {
            frm.doc.document_type.forEach(row => {
                update_selection_fields(frm, "Party Master Settings DocType", row.name);
            });
        }

        let grid = frm.fields_dict.document_type.grid;
        let wrapper = $(grid.parent);

        if (!wrapper.find('.custom-table-description').length) {
            wrapper.append(`
                <div class="custom-table-description" 
                    style="margin-top: 15px; padding: 15px;
                    background-color: #f8f9fa; border-radius: 3px;
                    border: 1px solid #dfe3e6;">
                    <h5 style="margin-bottom: 10px; color: #2e3b4a;">
                        ${__('Configuration Rules')}
                    </h5>
                    <ul style="color: #4a5660; list-style: disc; padding-left: 25px;">
                        <li>${__('Voucher Types must have a defined Party Master Field for validation')}</li>
                        <li>${__('Child Document Types require explicit Parent Doctype configuration')}</li>
                        <li>${__('System-generated Journal Entry Accounts bypass mandatory field checks')}</li>
                        <li>${__('Parent Doctype fields auto-lock for non-child document types')}</li>
                    </ul>
                </div>
            `);
        }

        // Fetch Party Types and update label
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Party Type",
                fields: ["name"]
            },
            callback: function(response) {
                if (response.message) {
                    const party_type_names = response.message.map(pt => pt.name).join(', ');
                    frm.set_df_property('is_party_master_mandatory', 'label', 
                        __('Is Party Master Mandatory') +
                        `<small class="text-muted">(${__('Applies to')}: ${party_type_names})</small>`
                    );
                }
            }
        });
    }
});

frappe.ui.form.on("Party Master Settings DocType", {
    form_render: function(frm, cdt, cdn) {
        update_selection_fields(frm, cdt, cdn); // Ensure dropdown updates when row renders
    },
    
    document_type: function(frm, cdt, cdn) {
        update_selection_fields(frm, cdt, cdn); // Update options when document_type changes
    }
});

function update_selection_fields(frm, cdt, cdn) {
    let row = locals[cdt][cdn]; // Get the row object
    if (!row.document_type) return;

    frappe.model.with_doctype(row.document_type, () => {
        let meta = frappe.get_meta(row.document_type);

        // Get valid fields for selection
        let fieldnames = meta.fields
            .filter(d => !frappe.model.no_value_type.includes(d.fieldtype))
            .map(d => ({ label: `${d.label} (${d.fieldname})`, value: d.fieldname }));

        // Update field options dynamically for the **specific row**
        let grid = frm.fields_dict.document_type.grid;
        let grid_row = grid.get_row(cdn);
        if (grid_row) {
            grid_row.get_field("party_fieldname").df.options = fieldnames.map(f => f.value).join("\n");
            grid_row.get_field("party_fieldname").refresh();
            
            grid_row.get_field("party_type_fieldname").df.options = fieldnames.map(f => f.value).join("\n");
            grid_row.get_field("party_type_fieldname").refresh();
        }

        // Preserve selected value if still valid, otherwise reset
        if (!fieldnames.find(f => f.value === row.party_fieldname)) {
            frappe.model.set_value(cdt, cdn, "party_fieldname", "");
        }

        if (row.is_dynamic_party_type) {
            if (!fieldnames.find(f => f.value === row.party_type_fieldname)) {
                frappe.model.set_value(cdt, cdn, "party_type_fieldname", "");
            }
        }
    });
}



/*
frappe.ui.form.on('Party Master Settings DocType', {
    document_type: function(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.document_type) {
            frappe.model.with_doctype(row.document_type, () => {
                let meta = frappe.get_meta(row.document_type);

                if (meta.istable) {
                    // For child tables: make parent_doctype required and editable
                    frappe.model.set_value(cdt, cdn, 'parent_doctype', '');
                } else {
                    // For non-child tables: auto-set and lock parent_doctype if empty
                    if (!row.parent_doctype) {
                        frappe.model.set_value(cdt, cdn, 'parent_doctype', row.document_type);
                    }
                }

                // Populate field options dynamically
                let fieldnames = meta.fields.filter(d => frappe.model.no_value_type.indexOf(d.fieldtype) === -1)
                    .map(d => ({ label: `${d.label} (${d.fieldname})`, value: d.fieldname }));

                frappe.model.set_value(cdt, cdn, 'party_fieldname', '');
                frm.fields_dict.document_type.grid.update_docfield_property("party_fieldname", "options", fieldnames);
            });
        }
    },

    is_dynamic_party_type: function(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.is_dynamic_party_type && row.document_type) {
            frappe.model.with_doctype(row.document_type, () => {
                let meta = frappe.get_meta(row.document_type);
                let options = meta.fields
                    .filter(d => frappe.model.no_value_type.indexOf(d.fieldtype) === -1)
                    .map(d => ({ label: `${d.label} (${d.fieldname})`, value: d.fieldname }));

                // Update party_type_fieldname options
                frappe.model.set_value(cdt, cdn, 'party_type_fieldname', '');
                frm.fields_dict.document_type.grid.update_docfield_property("party_type_fieldname", "options", options);
            });
        }
    }
});

*/