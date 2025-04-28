//import { $ } from "frappe-gantt/src/svg_utils";
uph.party_type_pm_rules = {};

function get_party_type_party_master_rules(party_type, callback) {
    if (Object.keys(uph.party_type_pm_rules).length === 0) {
        console.log("Fetching Party Type PM Rules");
        frappe.call({
            method: 'uph.party.doctype.party_master_settings.party_master_settings.get_party_type_party_master_rules_dict',
            callback: function (r) {
                if (r.message) {
                    Object.assign(uph.party_type_pm_rules, r.message);
                    console.log("Party Type PM Rules", uph.party_type_pm_rules);
                    callback(uph.party_type_pm_rules[party_type]);
                } else {
                    callback(null);
                }
            }
        });
    } else {
        callback(uph.party_type_pm_rules[party_type]);
    }
};



$(document).on("app_ready", function () {
    $.each(frappe.boot.party_account_types, function (p, a) {
        frappe.ui.form.on(p, {
            setup: function (frm) {
                frm.set_query("party_master", function (doc) {
                    return {
                        query: "uph.party.controllers.queries.party_master_link_query",
                        filters: {
                            party_type: frm.doc.doctype,
                        },
                    };
                });
                get_party_type_party_master_rules(frm.doc.doctype, function (rules) {
                    if (rules) {
                        frm.set_df_property("party_master", "reqd", rules.reqd);
                        frm.toggle_display("is_default_for_party_master", rules.allowed);
                        frm.allowed_set_default = rules.allowed;
                    }
                });
            },
            refresh: function (frm) {
                if (!frm.is_new()){
                    frm.toggle_enable('party_master',!frm.doc.party_master);
                    get_party_type_party_master_rules(frm.doc.doctype, function (rules) {
                        if (frm.doc.party_master && rules?.allowed) {
                            frm.add_custom_button(__("Reset As Default for Party Master"), function () {
                                frappe.call({
                                    method: "uph.party.controllers.party.set_party_as_default_for_party_master",
                                    args: {
                                        party: frm.doc.name,
                                        party_type: frm.doc.doctype,
                                        party_master: frm.doc.party_master,
                                        value: frm.doc.is_default_for_party_master ? 0 : 1,
                                    },
                                    freeze: true,
                                    callback: function (r) {
                                    if(!r.exc){
                                        frm.refresh();
                                    }
                                    }
                                });
                            }, __('Actions'));
                        }
                    });
                }
                if (!frm.is_new() && !frm.doc.party_master) {
                    frm.add_custom_button(__("Link to Party Master"), function () {
                        const d = new frappe.ui.Dialog({
                            title: __("Link to Party Master"),
                            fields: [
                                {
                                    label: __("Party Master"),
                                    fieldname: "party_master",
                                    fieldtype: "Link",
                                    options: "Party Master",
                                    reqd: 1,
                                    get_query: function () {
                                        return {
                                            query: "uph.party.controllers.queries.get_party_master",
                                            filters: {
                                                party_type: frm.doc.doctype,
                                            },
                                        };
                                    }
                                },
                            ],
                            primary_action_label: __("Link"),
                            freeze: 1,
                            primary_action(values) {
                                frm.set_value("party_master", values.party_master);
                                frm.save();
                                d.hide();
                                frm.reload();
                            },
                            secondary_action_label: __("Create new Party Master"),
                            secondary_action(frm) {
                                var dict= {
                                    Customer: frm.doc.customer_name,
                                    Supplier: frm.doc.supplier_name,
                                    Employee: frm.doc.employee_name,
                                  };
                                const pn = dict[p];
                                console.log("Party Name:", pn);
                                frappe.run_serially([
                                    ()=>d.hide(),
                                    ()=>erpnext.utils.create_new_doc("Party Master",{party_name:pn,party_type:frm.doc.doctype}),
                                ]);
                                
                            }
                        });
                        d.show();
                    });
                }else if(!frm.is_new()){
                    frm.add_custom_button(__("Parent Party :{0}",[frm.doc.party_master]), function () {
                        frappe.set_route("Form", "Party Master", frm.doc.party_master);
                    });
                    frm.add_custom_button(__("Unlink Party Master"), function () {
                        frappe.confirm(__("Are you sure you want to unlink this Party Master?"), function () {
                            frm.set_value("party_master", "");
                            frm.save();
                            frm.reload();
                        });
                    },__('Actions'));
                    frm.add_custom_button(__("Sync Party Master Details"), function () {
                        frappe.confirm(
                            __("This will synchronize all details from Party Master as configured in settings. Continue?"),
                            function () {
                                let args={
                                    source_name:frm.doc.party_master,
                                    target_doctype:frm.doc.doctype,
                                    target_doc:frm.doc.name,
                                    save:true,
                                }
                                frappe.call({
                                    method: "uph.party.doctype.party_master.party_master.create_party_from_party_master", // Replace with actual method path
                                    args: args,
                                    freeze: true, // Prevent user actions during the request
                                    freeze_message: __("Syncing details..."),
                                    callback: function (r) {
                                        if (!r.exc) {
                                            frappe.msgprint(__("Synchronization complete."));
                                            frm.reload();
                                        }
                                    },
                                    error: function (err) {
                                        console.error("Sync failed:", err);
                                        frappe.msgprint({
                                            title: __("Error"),
                                            message: __("Synchronization failed. Please check the console."),
                                            indicator: "red"
                                        });
                                    }
                                });
                            }
                        );
                    }, __("Actions"));
                    
                    }
            
            }
        });
        frappe.listview_settings[p] = {
            add_fields: ["party_master"],
            onload: function (listview) {
                if (listview.page.fields_dict.party_master) {
                    listview.page.fields_dict.party_master.get_query = function () {
                        return {
                            query: "uph.party.controllers.queries.get_party_master",
                            filters: {
                                party_type: listview.doctype,
                            },
                            
                        };
                    };
                }
            },
        };
        


    });
});
$(document).on("app_ready", function () {
    let doctypes=frappe.boot.party_master_on_doctypes_depend_field;
    $.each(doctypes, function (i, row) {
        let [doctype, child, fieldname] = row;
        if(doctype===child){

            (function(doctype, fieldname) {

            frappe.ui.form.on(doctype, {
                setup: function (frm) {
                    uph.party.setups(frm);
                },
                party_master: function(frm) {
                    uph.party.handle_party_master_change(frm,fieldname);
                    uph.party.set_party_query(frm,fieldname)
                },
                posting_date:function(frm){
                    if(!frm.fields_dict['posting_date'] ||!frm.doc?.posting_date) return;
                    uph.party.check_duplicate_party_master(frm);

                },
                refresh: function (frm) {
                    
                }
            });
        })(doctype, fieldname);

        }else if(doctype!==child && fieldname){
            (function(doctype, child, fieldname) {
                frappe.ui.form.on(doctype, {
                    setup: function (frm) {
                        uph.party.setup_queries_on_child(frm,child,fieldname);
                    },
                    
                    posting_date:function(frm){
                        if(!frm.fields_dict['posting_date'] ||!frm.doc?.posting_date) return;
                        uph.party.check_duplicate_party_master(frm);

                    },
                    
                });
                frappe.ui.form.on(child, {
                    party_master: function (frm, cdt, cdn) {
                        let row = locals[cdt][cdn];
                
                        if (!row.party_master) {
                            frappe.model.set_value(cdt, cdn, fieldname, '');
                            frm.refresh_field(frm.pm_on_child_fieldname);
                            return;
                        }
                
                        uph.party.show_party_selection_dialog_callback(frm, row.party_master, false,(values) => {
                            // Set returned values from dialog
                        
                            if (values) {
                                let grid = frm.fields_dict[frm.pm_on_child_fieldname].grid;

                                if (grid.get_field('party_type')) {
                                    frappe.model.set_value(cdt, cdn, 'party_type', values.party_type);
                                }
                                frappe.model.set_value(cdt, cdn, fieldname, values.party||values.name);
                                frm.refresh_field(frm.pm_on_child_fieldname);
                            }
                        });
                    }
                });
                
            })(doctype, child, fieldname);

        }
       
    });
});