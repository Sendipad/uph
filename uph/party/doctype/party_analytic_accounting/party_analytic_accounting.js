// Copyright (c) 2024, Abdo Ruzaqi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Party Analytic Accounting", {
    refresh(frm) {
        // Hide add-row buttons for parties child table
        hide_parties_add_button(frm);

        // Add custom button only if party_master exists
        if (frm.doc.party_master) {
            frm.fields_dict["parties"].grid.add_custom_button(
                __("Fetch Related Parties"),
                () => open_related_parties_dialog(frm)
            );
        }
    },

    parties_add(frm, cdt, cdn) {
        hide_parties_add_button(frm);
    },

    parties_remove(frm, cdt, cdn) {
        hide_parties_add_button(frm);
    },

    // ★ NEW: Enabled toggle logic
    enabled(frm) {
        if (!frm.doc.enabled) {
            // When disabled → automatically set status
            if (frm.doc.status !== "Inactive" && frm.doc.status !== "Archived") {
                frm.set_value("status", "Inactive");
            }
        } else {
            // Optional: when enabled, return status to Active if desired
            if (frm.doc.status === "Inactive" || frm.doc.status === "Archived") {
                frm.set_value("status", "Active");
            }
        }
    }
});

// Helper function
function hide_parties_add_button(frm) {
    frm.get_field("parties").grid.wrapper
        .find('.grid-add-row')
        .hide();
}


function open_related_parties_dialog(frm) {

    frappe.call({
        method: "uph.party.controllers.queries.get_party_master_parties",
        args: {
            party_master: frm.doc.party_master
        },
        callback(r) {
            if (!r.message || !r.message.length) {
                frappe.msgprint(__("No related parties found."));
                return;
            }

            let parties = r.message;

            // ------------------------------------------
            // (1) FILTER OUT ALREADY-EXISTING ROWS
            // ------------------------------------------
            let existing = frm.doc.parties || [];

            // keep only parties that are NOT in table
            let filtered = parties.filter(p => {
                return !existing.some(e =>
                    e.party_type === p.party_type &&
                    e.party === p.party
                );
            });

            // ------------------------------------------
            // (2) IF NOTHING LEFT → SHOW MESSAGE
            // ------------------------------------------
            if (!filtered.length) {
                frappe.msgprint(__("All related parties have already been added."));
                return;
            }

            // use filtered list instead of original
            parties = filtered;

            // ------------------------------------------
            // (3) OPEN DIALOG WITH FILTERED ROWS ONLY
            // ------------------------------------------
            const dialog = new frappe.ui.Dialog({
                title: __("Select Parties to Add"),
                size: "large",
                fields: [
                    {
                        fieldname: "parties_table",
                        label: __("Parties"),
                        fieldtype: "Table",
                        cannot_add_rows: true,
                        in_place_edit: false,
                        fields: [
                            { fieldtype: "Link", fieldname: "party_type", label: __("Party Type"), options: "DocType", in_list_view: 1, read_only: 1 },
                            { fieldtype: "Dynamic Link", fieldname: "party", label: __("Party"), options: "party_type", in_list_view: 1, read_only: 1 },
                            { fieldtype: "Data", fieldname: "party_name", label: __("Name"), read_only: 1, in_list_view: 1 }
                        ],
                        data: parties,
                        get_data: () => parties
                    }
                ],
                primary_action_label: __("Add Selected"),
                primary_action(values) {

                    let selected = dialog.fields_dict.parties_table.grid.get_selected_children();

                    if (!selected.length) {
                        frappe.msgprint(__("Please select at least one party."));
                        return;
                    }

                    selected.forEach(row => {
                        let child = frm.add_child("parties");
                        child.party_type = row.party_type;
                        child.party = row.party;
                    });

                    frm.refresh_field("parties");
                    dialog.hide();
                }
            });

            dialog.show();
        }
    });
}




