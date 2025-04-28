// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt
 frappe.ui.form.on("Party Master Settings", {
    onload:function(frm){
      frm.fields_dict['party_types'].grid.cannot_add_rows = true;
      frm.refresh_field(party_types);
    },
    refresh(frm) {
            frm.refresh_field('document_types');
            if (frm.doc.document_types && frm.doc.document_types.length) {
                frm.doc.document_types.forEach(row => {
                    update_selection_fields(frm, "Party Master Settings DocType", row.name);
                });
            }
    
            let grid = frm.fields_dict.document_types.grid;
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
     
        }
    });
    frappe.ui.form.on("Party Master Settings Party Type", {
        refresh:function(frm,cdt,cdn){
            let row = locals[cdt][cdn];
            if(!row.party_type) return;
            if(!row.allowed) return;
          

        },
        allowed:function(frm,cdt,cdn){
            let row = locals[cdt][cdn];
            if(!row.party_type || row.allowed===0) return;
            if(row.allowed===1){
                frappe.model.with_doctype(row.party_type,()=>{
                    let meta = frappe.get_meta(row.party_type);
                    let fieldnames = meta.fields
                        .filter(d => !frappe.model.no_value_type.includes(d.fieldtype))
                        .map(d => ({ label: `${d.label} (${d.fieldname})`, value: d.fieldname }));
                    let grid = frm.fields_dict.party_types.grid;
                    let grid_row = grid.get_row(row.name);
                    if (grid_row) {
                        grid_row.get_field("rule_fieldname").df.options = fieldnames.map(f => f.value).join("\n");
                        grid_row.get_field("rule_fieldname").refresh();
                       
                    }
                });
                }
            
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
            let grid = frm.fields_dict.document_types.grid;
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
    
    
    
 	
