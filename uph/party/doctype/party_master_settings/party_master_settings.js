// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt
frappe.ui.form.on("Party Master Settings", {
    onload: function (frm) {
        // Prevent adding/removing rows for party_types grid
        if (frm.fields_dict['party_types']?.grid) {
            frm.fields_dict['party_types'].grid.cannot_add_rows = true;
            frm.fields_dict['party_types'].grid.cannot_delete_rows = true;
            // Refresh with string literal
            frm.refresh_field('party_types');
        }
    },

    refresh: function (frm) {
        // Refresh the document_types grid
        frm.refresh_field('document_types');

        // Update selection fields for existing rows
        if (frm.doc.document_types && frm.doc.document_types.length) {
            frm.doc.document_types.forEach(row => {
                update_selection_fields(frm, "Party Master Settings DocType", row.name);
            });
        }

        // Add description to document_types grid (only once)
        let grid = frm.fields_dict.document_types?.grid;
        if (grid) {
            let wrapper = $(grid.parent);
            if (!wrapper.find('.custom-table-description').length) {
                wrapper.append(`
                    <div class="custom-table-description" 
                        style="margin-top: 15px; padding: 15px; background-color: #f8f9fa; 
                               border-radius: 3px; border: 1px solid #dfe3e6;">
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
        }
    }
});

frappe.ui.form.on("Party Master Settings Party Type", {
    form_render: function (frm, cdt, cdn) {
        update_party_type_rule_field(frm, cdt, cdn);
    },
    allowed: function (frm, cdt, cdn) {
        update_party_type_rule_field(frm, cdt, cdn);
    }
});


frappe.ui.form.on("Party Master Settings DocType", {
    form_render: function (frm, cdt, cdn) {
        update_selection_fields(frm, cdt, cdn);
    },

    document_type: function (frm, cdt, cdn) {
        update_selection_fields(frm, cdt, cdn);
    }
});

function update_selection_fields(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (!row.document_type) return;

    frappe.model.with_doctype(row.document_type, () => {
        let meta = frappe.get_meta(row.document_type);

        let fieldnames = meta.fields
            .filter(d => !frappe.model.no_value_type.includes(d.fieldtype))
            .map(d => d.fieldname);

        let grid = frm.fields_dict.document_types?.grid;
        if (!grid) return;

        let grid_row = grid.get_row(cdn);
        if (!grid_row) return;

        // Update field options (for Select fields)
        const party_field = grid_row.get_field("party_fieldname");
        if (party_field) {
            party_field.df.options = fieldnames.join("\n");
            party_field.refresh();
        }

        const party_type_field = grid_row.get_field("party_type_fieldname");
        if (party_type_field) {
            party_type_field.df.options = fieldnames.join("\n");
            party_type_field.refresh();
        }

        // Validate existing values
        if (row.party_fieldname && !fieldnames.includes(row.party_fieldname)) {
            frappe.model.set_value(cdt, cdn, "party_fieldname", "");
        }

        if (row.is_dynamic_party_type && row.party_type_fieldname &&
            !fieldnames.includes(row.party_type_fieldname)) {
            frappe.model.set_value(cdt, cdn, "party_type_fieldname", "");
        }
    });
}



function update_party_type_rule_field(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (!row.party_type || row.allowed === 0) return;

    frappe.model.with_doctype(row.party_type, () => {
        let meta = frappe.get_meta(row.party_type);
        let fieldnames = meta.fields
            .filter(d => !frappe.model.no_value_type.includes(d.fieldtype))
            .map(d => d.fieldname);

        let grid = frm.fields_dict.party_types.grid;
        let grid_row = grid.get_row(row.name);

        if (grid_row) {
            let field = grid_row.get_field("rule_fieldname");
            if (field) {
                field.df.options = fieldnames.join("\n");
                field.refresh();
            }
        }
    });
}
