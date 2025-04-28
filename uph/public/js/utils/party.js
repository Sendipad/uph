frappe.provide("uph.party");

const SALES_DOCTYPES = ["Quotation", "Sales Order", "Delivery Note", "Sales Invoice", "POS Invoice"];
const PURCHASE_DOCTYPES = ["Supplier Quotation", "Purchase Order", "Purchase Receipt", "Purchase Invoice"];
let uphdialog=null;
uph.party = {
    show_party_selection_dialog_callback: function (frm, party_master,force_show=false, callback) {
        if(frm.in_show_party_selection)return;
        let filters={party_master:party_master};
        if(frm.is_single_party_type &&frm.party_type){
            filters.party_type=frm.party_type;
        }

        frappe.call({
            method: 'uph.party.controllers.queries.get_party_master_parties',
            args: filters,
            callback: function (r) {
                if (r.message) {
                    let parties = r.message;
                    console.log('First:',parties);
                    if (parties.length === 0) {
                        frappe.msgprint(__('Party Master has no Parties Linked'));
                        return;
                    }
                    if(parties.length==1){
                        return callback(parties[0]);
                    }else if (frm.is_single_party_type){
                        let selected_party=parties.find(p=>p.is_default===1);
                        if(selected_party){
                            return callback(selected_party);

                        }

                    }
                    if (!uphdialog) {
                        console.log("First Creation Dialog");
                        uphdialog = new frappe.ui.Dialog({
                            title: __("Select Party"),
                            fields: [
                                
                                {
                                    fieldname: "party",
                                    fieldtype: "Select",
                                    label: __("Select Party"),
                                    options: [],
                                    
                                },
                                {
                                    fieldname: "party_type",
                                    fieldtype: "Select",
                                    label: __("Select Party Type"),
                                    options: [],
                                },
                                { fieldtype: "Column Break" },
                                { fieldname: "party_name", fieldtype: "Data", label: __("Name"), read_only: 1 },
                                { fieldname: "currency", fieldtype: "Link", options: "Currency", read_only: 1 },
                                {fieldtype:"Section Break"},
                                {fieldname:"is_default_for_party_master",fieldtype:"Check",hidden:1,label:"Set As Default"}
                            ],
                            
                        });
                    }
                    let party_type=[...new Set(parties.map(p => p.party_type))];
                    uphdialog.set_df_property("party","options",parties.map(p => p.party));
                    
                    uphdialog.set_value("party_name","");
                    uphdialog.set_value("party",parties[0].party);
                    uphdialog.fields_dict.party.df.onchange=function(){
                    
                            let selected_party = uphdialog.get_value("party");
                            let party_data = parties.find(p => p.party === selected_party);
                            if (party_data) {
                                uphdialog.set_value('currency', party_data.currency);
                                uphdialog.set_value('party_name', party_data.party_name);
                                uphdialog.set_value('party_type', party_data.party_type);
                            }
                        }
                    

                    
                    if (party_type.length==1){
                        uphdialog.set_value("party_type",party_type[0]);
                        uphdialog.set_df_property("party_type","read_only",1);


                    }else if (party_type.length>1){
                        uphdialog.set_df_property("party_type","read_only",0);
                        uphdialog.set_df_property("party_type", "options", party_type);
                        uphdialog.set_value("party_type",party_type[0]);
                        /*uphdialog.fields_dict.party_type.df.onchange=function(){
                    
                            let selected_pt = uphdialog.get_value("party_type");
                            let party_data = parties.filter(p => p.party_type === selected_pt);
                            if (party_data) {
                                let party=party_data.map(p => p.name);
                                uphdialog.set_df_property("party","options",party);
                            }
                        }*/
                    }             
                    uphdialog.set_df_property("is_default_for_party_master", "hidden", 1)
                    if (SALES_DOCTYPES.includes(frm.doc.doctype)||PURCHASE_DOCTYPES.includes(frm.doc.doctype)){
                        uphdialog.set_df_property("is_default_for_party_master", "hidden", 0);
                    
                    }
                    uphdialog.refresh();
                    uphdialog.show();
                    uphdialog.set_primary_action(__("Set Party"), () => {
                        let values = uphdialog.get_values();
                        if (values.is_default_for_party_master){
                            frappe.call({
                                method:"uph.party.controllers.party.set_party_as_default_for_party_master",
                                args:{
                                    party:values.party,
                                    party_type:values.party_type,
                                    party_master:party_master,
                                    value:values.is_default_for_party_master

                                },
                                callback:function(r){
                                    if (!r.exc){
                                        frappe.msgprint({message:__('Successfully Set {0} as Default for {1}',[values.party,party_master]),alert:true});
                                    }
                                    //if error then show else alert update successfully
                                }
                            });
                        }
                        frappe.run_serially([
                            ()=> callback(values),
                            ()=> uphdialog.hide()
                        ]);

                        


                    });
                }
            }
            });
        },
    get_fieldnames: function(frm) {
        if (SALES_DOCTYPES.includes(frm.doc.doctype)) {
            return { party_type: 'Customer', party_fieldname: 'customer', default_role_fieldname: 'default_customer' };
        }
        if (PURCHASE_DOCTYPES.includes(frm.doc.doctype)) {
            return { party_type: 'Supplier', party_fieldname: 'supplier', default_role_fieldname: 'default_supplier' };
        }
        if (frm.doc.doctype === 'Payment Entry') {
            return { party_type: frm.doc.party_type, party_fieldname: 'party', isdynamic: 1 };
        }
        return {};
    },

    pm_base_filter: function(frm) {
        let pt = this.get_fieldnames(frm);
        return {
            doctype: frm.doc.doctype,
            reference_doctype: frm.doc.doctype,
            disabled: 0,
            is_group: 0,
            party_type: pt.party_type
        };
    },

    make_party_from_party_master_factory: function(frm) {
        let party_type = [frm.doc.party_type];
    
        if (frm.doc.roles && frm.doc.roles.length > 0) {
            party_type = [...new Set([frm.doc.party_type, ...frm.doc.roles.map(role => role.party_type_role)])];
        }
    
        // Factory function to create a new dialog instance
        const create_dialog = () => {
            return new frappe.ui.Dialog({
                title: __("Create Party"),
                fields: [
                    {
                        fieldname: "party_type",
                        fieldtype: "Select",
                        label: __("Select Party Type"),
                        options: party_type,
                    },
                    {
                        fieldname: "default_currency",
                        fieldtype: "Select",
                        label: __("Default Currency"),
                        options: erpnext.get_presentation_currency_list(),
                    }
                ],
                primary_action_label: __("Create & Save"),
                primary_action(values) {
                    let args = {
                        source_name: frm.doc.name,
                        target_doctype: values.party_type || frm.doc.party_type,
                        rule_field_value: values.default_currency,
                        save: true,
                    };
                    frappe.call({
                        method: 'uph.party.doctype.party_master.party_master.map_party_to_target',
                        args: args,
                        callback(r) {
                            if (r.message) {
                                dialog.hide();
                                frappe.msgprint(__("Party Created Successfully"));
                            }
                        }
                    });
                },
                secondary_action_label: __("Edit in Full Form"),
                secondary_action(values) {
                    let args = {
                        source_name: frm.doc.name,
                        target_doctype: values.party_type || frm.doc.party_type,
                        rule_field_value: values.default_currency,
                    };
                    frappe.call({
                        method: 'uph.party.doctype.party_master.party_master.map_party_to_target',
                        args: args,
                        callback(r) {
                            if (r.message) {
                                dialog.hide();
                                frappe.model.sync(r.message);
                                frappe.set_route("Form", "Customer", r.message.name);
                            }
                        }
                    });
                }
            });
        };
    
        // Create and show dialog
        const dialog = create_dialog();
    
        dialog.set_value('party_type', party_type[0]);
    
        // Add onchange handler for dynamic behavior
        dialog.fields_dict.party_type.df.onchange = function () {
            let target_doctype = dialog.get_value('party_type');
            get_party_type_party_master_rules(target_doctype, function (rules) {
                if (!rules.allowed) {
                    dialog.set_df_property("default_currency", "hidden", 1);
                } else if (rules.allowed && rules.rule_fieldname == "default_currency") {
                    dialog.set_df_property("default_currency", "hidden", 0);
                    dialog.set_df_property("default_currency", "reqd", 1);
                }
            });
        };
    
        dialog.show();
    },






    party_master_query: function(frm) {
        let filters={

        }
        if (frm.is_single_party_type && frm.party_type){
            filters.party_type=frm.party_type;
        }
        frm.set_query('party_master', () => ({
            query: "uph.party.controllers.queries.party_master_link_query",
            filters: filters
        }));
    },

    party_analytic_accounting_query: function(frm) {
        if (frm.fields_dict.party_analytic_accounting && frm.doc.party_master) {
            frm.set_query('party_analytic_accounting', () => ({
                filters: { party_master: frm.doc.party_master }
            }));
        }
    },

    set_party_query: function(frm, fieldname) {
        let filters={};
        if (frm.doc.party_master){
            filters.party_master=frm.doc.party_master;
        }
        frm.set_query(fieldname, () => ({
            filters: filters,
        }));
        frm.refresh_field(fieldname);
    },

    get_default: function(frm, fn) {
        fn = fn || this.get_fieldnames(frm);
        if (!frm.get_default_partyRole || !frm.doc.party_master || !fn.default_role_fieldname) return;

        frappe.db.get_value("Party Master", frm.doc.party_master, fn.default_role_fieldname, (r) => {
            if (r && r.message) {
                frm.pass_selections_dialog = true;
                frm.set_value(fn.party_fieldname, r.message[fn.default_role_fieldname]);
                frm.refresh_field(fn.party_fieldname);
                frm.pass_selections_dialog = false;
            }
        });
    },

    get_dialog_field: function(frm, pm_details, fn) {
        const partyTypes = Array.isArray(pm_details.party_type_roles) 
            ? pm_details.party_type_roles 
            : [pm_details.party_type_roles || fn.party_type];
        
        const parties = pm_details.parties || [];
        const currencyLabel = parties.some(p => p.currency) ? __(' (Currency)') : '';

        const fields = [
            { 
                fieldname: "party_type", 
                fieldtype: "Select", 
                label: __("Select Party Type"), 
                options: partyTypes.map(p => __(p)),
                default: partyTypes[0],
                read_only: fn.isdynamic ? 0 : 1,
                // Add this hidden property
                hidden: partyTypes.length === 1  // Hide if only one party type
            },
            { 
                fieldname: "party", 
                fieldtype: "Select", 
                label: __("Select Party"), 
                options: parties.map(p => `${p.name}${p.currency ? ` (${p.currency})` : ''}`)
            }
        ];

        if (frm.get_default_partyRole && fn.default_role_fieldname) {
            fields.push({
                label: __('Set As Default {0}', [fn.party_type]),
                fieldname: fn.default_role_fieldname,
                fieldtype: 'Check',
                default: 0,
                //hidden: fn.isdynamic ? 1 : 0
            });
        }

        return fields;
    },

    show_selection_dialog: function(frm, pm_details, fn, callback) {
        const parties = pm_details.parties || [];
        
        if (parties.length === 0) {
            frappe.msgprint(__('Party Master has no Parties Linked'));
            return;
        }
        if (frm.in_show_party_selections)return;
        fn = fn || this.get_fieldnames(frm);
        const fields = this.get_dialog_field(frm, pm_details, fn);
        
        const d = new frappe.ui.Dialog({
            title: __("Select a Party"),
            fields: fields,
            primary_action_label: __("Select"),
            primary_action: function(values) {
                if (!values.party) {
                    frappe.throw(__("Please select a party."));
                }
    
                // Find the selected party object
                const selectedParty = parties.find(p => 
                    `${p.name}${p.currency ? ` (${p.currency})` : ''}` === values.party
                );
    
                if (!selectedParty) {
                    frappe.throw(__("Invalid selection. Please choose a valid party."));
                }
    
                // Set the selected party in the form
                frm.set_value(fn.party_fieldname, selectedParty.name);
    
                // If user wants to set this as the default party, update Party Master properly
                if (values[fn.default_role_fieldname]) {
                    frappe.call({
                        method: "frappe.client.get",
                        args: {
                            doctype: "Party Master",
                            name: frm.doc.party_master
                        },
                        callback: function(r) {
                            if (r.message) {
                                let party_master_doc = r.message;
                                party_master_doc[fn.default_role_fieldname] = selectedParty.name;
    
                                // Save the updated document
                                frappe.call({
                                    method: "frappe.client.save",
                                    args: { doc: party_master_doc },
                                    callback: function(save_res) {
                                        if (!save_res.exc) {
                                            frappe.msgprint(__("Default set successfully"));
                                        } else {
                                            frappe.msgprint(__("Error saving document: {0}", [save_res.exc]));
                                        }
                                    }
                                });
                            }
                        }
                    });
                }
    
                d.hide();
                frm.in_show_party_selections=false;
                if (callback) callback();
            }
        });
        frm.in_show_party_selections=true;
        d.show();
    },    

    get_party_master_details: function(frm, fn, callback) {
        const args = { 
            party_master: frm.doc.party_master, 
            party_type: fn.isdynamic ? frm.doc.party_type : fn.party_type 
        };

        frappe.call({
            method: "uph.party.controllers.party.get_party_master_details_with_parties",
            args: args,
            callback: (r) => {
                if (r.exc) {
                    frappe.msgprint(__("Failed to load Party Master details."));
                    return;
                }

                const pm_details = r.message || {};
                pm_details.parties = pm_details.parties || [];
                pm_details.party_type_roles = Array.isArray(pm_details.party_type_roles)
                    ? pm_details.party_type_roles
                    : [pm_details.party_type_roles || fn.party_type];

                callback(pm_details);
            }
        });
    },

    handle_party_master_change: function(frm,fieldname) {
        if (!frm.doc.party_master) return;
        this.show_party_selection_dialog_callback(frm,frm.doc.party_master,false, (values) => {
            // Set returned values from dialog
            if (values) {
                if(!frm.is_single_party_type && frm.fields_dict['party_type']){
                    frm.set_value('party_type', values.party_type);
                    frm.refresh_field('party_type');
                }
                frm.set_value(fieldname,values.party||values.name);
                frm.refresh_field(fieldname);
            }
        });
        this.check_duplicate_party_master(frm);
    },

    finalize_pm_details: function(frm, pm_details) {
        const enforceField = 'enforce_party_analytic_accounting_selection'; // Fixed typo
        if (pm_details[enforceField] && frm.fields_dict.party_analytic_accounting) {
            frm.toggle_reqd('party_analytic_accounting', true);
        } else if (frm.fields_dict.party_analytic_accounting) {
            frm.toggle_reqd('party_analytic_accounting', false);
        }
    },

    on_party_field_change: function(frm, fn) {
        if (frm.doc.party_master && frm.doc.party_master !='') return;

        fn = fn || this.get_fieldnames(frm);
        const partyType = frm.doc[fn.party_type];
        const party = frm.doc[fn.party_fieldname];

        if (!partyType || !party) return;

        frappe.db.get_value(partyType, party, "party_master", (r) => {
            if (r?.message?.party_master) {
                frm.set_value("party_master", r.message.party_master);
                frm.refresh_field("party_master");
            }
        });
    },
    setup_queries_on_child: function(frm, child_doctype, fieldname) {
        let child_fieldname = null;
        frm.in_show_party_selection=false;
        // Loop through all fields in the form
        frm.meta.fields.forEach(df => {
            if (df.fieldtype === "Table" && df.options === child_doctype) {
                child_fieldname = df.fieldname;
                frm.pm_on_child_fieldname=child_fieldname;
            }
        });
    
        if (child_fieldname) {
            console.log("Found child fieldname:", frm.pm_on_child_fieldname);
    
            // Example: setting a query on a field inside the child table
            frm.fields_dict[child_fieldname].grid.get_field('party_master').get_query = function(doc, cdt, cdn) {
                return {
                    query: "uph.party.controllers.queries.party_master_link_query",

                    filters: {

                        /* your filter logic */
                    }
                };
            };
            frm.fields_dict[child_fieldname].grid.get_field(fieldname).get_query = function(doc, cdt, cdn) {
                let row = locals[cdt][cdn];
                return {
                    filters: {
                        party_master: row.party_master  // assuming this is the field in the link doctype
                    }
                };
            };
        frm.refresh_field(child_doctype);
        } 
    },
    show_selection_dialog_callback: function (frm, party_master, callback) {
        if(frm.in_show_party_selection)return;
        let filters={party_master:party_master};
        if(frm.is_single_party_type &&frm.party_type){
            filters.party_type=frm.party_type;
        }
        frappe.call({
            method: 'uph.party.controllers.queries.get_party_master_parties',
            args: filters,
            callback: function (r) {
                if (r.message) {
                    let parties = r.message;
                    console.log('First:',parties);
    
                    if (parties.length === 0) {
                        frappe.msgprint(__('Party Master has no Parties Linked'));
                        return;
                    }
                    if(parties.length==1 || frm.is_single_party_type &&parties[0].is_default==1){
                        return callback(parties[0]);
                    }
                    let is_initializing_dialog = true;
                    let dialog = new frappe.ui.Dialog({
                        title: __("Select Party"),
                        fields: [
                           
                            {
                                fieldname: "party",
                                fieldtype: "Select",
                                label: __("Select Party"),
                                options: parties.map(p => p.name),
                                onchange: function () {
                                    if (is_initializing_dialog) return;
        
                                    let selected_party = this.get_value();
                                    let party_data = parties.find(p => p.name === selected_party);
        
                                    if (party_data) {
                                        dialog.set_value('currency', party_data.currency);
                                        dialog.set_value('party_name', party_data.party_name);
                                        dialog.set_value('party_type', party_data.party_type);
                                    }
                                }
                            },
                            {
                                fieldname: "party_type",
                                fieldtype: "Select",
                                label: __("Select Party Type"),
                                options: [...new Set(parties.map(p => p.party_type))],
                                read_only:1, // Unique party types
                            },
                            { fieldtype: "Column Break" },
                            { fieldname: "party_name", fieldtype: "Data", label: __("Name"), read_only: 1 },
                            { fieldname: "currency", fieldtype: "Link", options: "Currency", read_only: 1 }
                        ],
                        primary_action_label: __("Set"),
                        primary_action(values) {
                            if (!values || !values.party) {
                                frappe.msgprint(__("You must select a party."));
                                return;
                            }
                            frappe.run_serially([
                                () => callback(values),
                                () => dialog.hide(),
                                ()=>frm.in_show_party_selection=false
                            ]);
                        }
                    });
                        //frm.in_show_party_selection=true,

               // Show and then set values with flag ON
               dialog.show();

               dialog.set_value('party', parties[0].name);
               dialog.set_value('party_type', parties[0].party_type);
               dialog.set_value('party_name', parties[0].party_name);
               dialog.set_value('currency', parties[0].currency);
               is_initializing_dialog = false;

               // ✅ Now allow onchange to run
                   
                }
            }
        });
    },

        
                    
                       
    setups: function(frm) {
        if(SALES_DOCTYPES.includes(frm.doc.doctype)){
            frm.is_single_party_type=true;
            frm.party_type="Customer";
        }else if(PURCHASE_DOCTYPES.includes(frm.doc.doctype)){
            frm.is_single_party_type=true;
            frm.party_type="Supplier";
        }else{
            frm.is_single_party_type=false;

        }
        frm.in_show_party_selections=false;


        this.party_master_query(frm);
        this.party_analytic_accounting_query(frm);
    },
    check_duplicate_party_master: function(frm, triggered_before_submit = false) {
        if (!frm.doc.party_master || !frm.doc.posting_date) return;
    
        let args = {
            party_master: frm.doc.party_master,
            doctype: frm.doc.doctype,
            posting_date: frm.doc.posting_date,
            current_name: frm.doc.name || undefined
        };
    
        if (triggered_before_submit) {
            args.doc = frm.doc;
        }
    
        frappe.call({
            method: "uph.party.controllers.party.check_duplicate_voucher_party_master",
            args: args,
            callback: function(r) {
                if (!r.exc && r.message && r.message.duplicates) {
                    const duplicates = r.message.duplicates;
                    if (duplicates.length > 0) {
                        const msg = __("Warning: Found {0} existing document(s) with the same Party Master and posting date:", [duplicates.length]);
                        const list = duplicates.map(d => `
                            <li style="margin-bottom: 10px;">
                                <a href="/app/${frappe.router.slug(frm.doctype)}/${encodeURIComponent(d.name)}" 
                                   target="_blank">
                                    ${d.name}
                                </a>
                                <span  
                                   class="text-muted">
                                (${d.party})    (${d.total})</span>
                            </li>
                        `).join('');
    
                        if (triggered_before_submit) {
                            // Confirmation before submit
                            frappe.confirm({
                                title: __('Duplicate Warning'),
                                indicator: 'red',
                                message: `${msg}<ul>${list}</ul>`,
                                as_html: true,
                                primary_action_label: __('Proceed Anyway'),
                                primary_action: () => {
                                    frappe.call({
                                        method: "uph.party.controllers.party.allow_duplicate_submission",
                                        args: {
                                            doctype: frm.doctype,
                                            docname: frm.doc.name
                                        },
                                        callback: (response) => {
                                            if (!response.exc) {
                                                frm.save();
                                            }
                                        }
                                    });
                                },
                                secondary_action_label: __('Cancel')
                            });
                        } else if (frm.is_new()) {
                            // Dialog for new documents
                            const d = new frappe.ui.Dialog({
                                title: __('Duplicate Documents Found'),
                                fields: [
                                    {
                                        fieldtype: 'HTML',
                                        fieldname: 'message',
                                        options: `<div class="alert alert-warning">${msg}</div>`
                                    },
                                    {
                                        fieldtype: 'HTML',
                                        fieldname: 'list',
                                        options: `<ul style="max-height: 200px; overflow-y: auto;">${list}</ul>`
                                    },
                                    {
                                        label: __('Change Posting Date'),
                                        fieldtype: 'Date',
                                        fieldname: 'posting_date',
                                        default: frm.doc.posting_date,
                                        reqd: 1
                                    }
                                ],
                                primary_action_label: __('Update Date'),
                                primary_action: (values) => {
                                    if (values.posting_date) {
                                        if (values.posting_date===frm.doc.posting_date){
                                            frm.set_intro(`${__('There Are Some Duplicate:')} ${duplicates.length } <ul>${list}</ul>`, 'red');

                                        }else{
                                            frm.set_value('posting_date', values.posting_date);
                                            frm.refresh_field('posting_date');
                                        }
                                       
                                    }
                                    d.hide();
                                }
                            });
                            d.show();
                        } else {
                            // Message for existing documents
                            frappe.msgprint({
                                title: __('Duplicate Warning'),
                                indicator: 'red',
                                message: `${msg}<ul>${list}</ul>`,
                                as_html: true,
                                alert: true
                            });
                        }
                    }
                }
            }
        });
    },

}
/*
    check_duplicate_party_master: function(frm, triggered_before_submit = false) {
        if (!frm.doc.party_master || !frm.doc.posting_date) return;

        frappe.call({
            method: "uph.party.controllers.party.check_party_master_duplicates",
            args: this.get_args(frm, triggered_before_submit),
            callback: (r) => this.handle_response(frm, r, triggered_before_submit)
        });
    },

    get_args: function(frm, triggered_before_submit) {
        return {
            party_master: frm.doc.party_master,
            doctype: frm.doc.doctype,
            posting_date: frm.doc.posting_date,
            current_name: frm.doc.name || undefined,
            doc: triggered_before_submit ? frm.doc : undefined
        };
    },

    handle_response: function(frm, response, triggered_before_submit) {
        if (response.exc || !response.message?.duplicates?.length) return;

        const duplicates = response.message.duplicates.map(dup => ({
            ...dup,
            matches: dup.matches || { parent: [], children: {} },
            details: this.format_details(dup.matches)
        }));

        if (triggered_before_submit) {
            this.show_submit_dialog(frm, duplicates);
        } else {
            this.show_alert(frm, duplicates);
        }
    },

    format_details: function(matches) {
        const safeMatches = matches || { parent: [], children: {} };
        return [
            this.format_parent_matches(safeMatches.parent),
            this.format_child_matches(safeMatches.children)
        ].filter(Boolean).join('');
    },

    format_parent_matches: function(parentMatches) {
        if (!parentMatches?.length) return '';
        
        return `
            <div class="duplicate-section">
                <h6>${__("Matching Fields")}:</h6>
                <ul class="list-unstyled">
                    ${parentMatches.map(m => `
                        <li>${m.label}: <strong>${m.value}</strong></li>
                    `).join('')}
                </ul>
            </div>
        `;
    },

    format_child_matches: function(childMatches) {
        if (!childMatches) return '';
        
        return Object.entries(childMatches).map(([label, data]) => `
            <div class="duplicate-section">
                <h6>${label}:</h6>
                <div class="text-muted small">
                    ${data.matched ? 
                        __("All items match") : 
                        __("{0} vs {1} items", [data.current_count, data.existing_count])}
                </div>
            </div>
        `).join('');
    },

    show_submit_dialog: function(frm, duplicates) {
        duplicates.forEach(dup => {
            const dialog = new frappe.ui.Dialog({
                title: __('Duplicate Detected'),
                size: 'large',
                fields: [{
                    fieldtype: 'HTML',
                    fieldname: 'content',
                    options: this.get_dialog_content(frm, dup)
                }],
                primary_action: () => this.submit_override(frm, dialog),
                primary_action_label: __('Submit Anyway')
            });
            dialog.show();
        });
    },

    get_dialog_content: function(frm, dup) {
        return `
            <div class="duplicate-warning">
                <a href="${frappe.utils.get_form_url(frm.doctype, dup.name)}" 
                   target="_blank" class="bold">
                    ${dup.name}
                </a>
                <div class="text-muted small mt-2">
                    ${__("Created by")} ${dup.owner} • 
                    ${frappe.datetime.str_to_user(dup.posting_date)}
                </div>
                ${dup.details}
            </div>
        `;
    },

    submit_override: function(frm, dialog) {
        frappe.call({
            method: "uph.party.controllers.party.allow_duplicate_submission",
            args: { doctype: frm.doctype, name: frm.doc.name },
            callback: () => {
                frm.save();
                dialog.hide();
            }
        });
    },

    show_alert: function(frm, duplicates) {
        duplicates.forEach(dup => {
            frappe.msgprint({
                title: __('Possible Duplicate'),
                indicator: 'orange',
                message: `
                    <div class="duplicate-warning">
                        <a href="${frappe.utils.get_form_url(frm.doctype, dup.name)}" 
                           target="_blank" class="bold">
                            ${dup.name}
                        </a>
                        ${dup.details}
                    </div>
                `,
                as_html: true
            });
        });
    }
};

frappe.ui.add_css(`
    .duplicate-warning {
        border-left: 3px solid #ff5858;
        padding: 15px;
        margin: 15px 0;
        background: #fff8f8;
    }
    .duplicate-section {
        margin: 15px 0;
        padding: 10px;
        background: #f9f9f9;
        border-radius: 4px;
    }
    .duplicate-section h6 {
        margin: 0 0 8px 0;
        font-size: 13px;
        color: #2e3338;
    }
`);*/



    /*
    check_duplicate_party_master: function(frm, triggered_before_submit = false) {
        if (!frm.doc.party_master || !frm.doc.posting_date) return;
    
        let args = {
            party_master: frm.doc.party_master,
            doctype: frm.doc.doctype,
            posting_date: frm.doc.posting_date,
            current_name: frm.doc.name || undefined
        };
    
        if (triggered_before_submit) {
            args.doc = frm.doc;
        }
    
        frappe.call({
            method: "uph.party.controllers.party.check_party_master_duplicates",
            args: args,
            callback: function(r) {
                if (!r.exc && r.message && r.message.duplicates) {
                    const duplicates = r.message.duplicates;
                    if (duplicates.length > 0) {
                        const msg = __("Warning: Found {0} existing document(s) with the same Party Master and posting date:", [duplicates.length]);
                        const list = duplicates.map(d => `
                            <li style="margin-bottom: 10px;">
                                <a href="/app/${frappe.router.slug(frm.doctype)}/${encodeURIComponent(d.name)}" 
                                   target="_blank" 
                                   class="text-muted">
                                    ${d.name}
                                </a>
                                (${d.owner}) (${d.party}) (${d.total})
                            </li>
                        `).join('');
    
                        if (triggered_before_submit) {
                            // Confirmation before submit
                            frappe.confirm({
                                title: __('Duplicate Warning'),
                                indicator: 'red',
                                message: `${msg}<ul>${list}</ul>`,
                                as_html: true,
                                primary_action_label: __('Proceed Anyway'),
                                primary_action: () => {
                                    frappe.call({
                                        method: "uph.party.controllers.party.set_pass_duplicate_check_before_submit",
                                        args: {
                                            doctype: frm.doctype,
                                            docname: frm.doc.name
                                        },
                                        callback: (response) => {
                                            if (!response.exc) {
                                                frm.save();
                                            }
                                        }
                                    });
                                },
                                secondary_action_label: __('Cancel')
                            });
                        } else if (frm.is_new()) {
                            // Dialog for new documents
                            const d = new frappe.ui.Dialog({
                                title: __('Duplicate Documents Found'),
                                fields: [
                                    {
                                        fieldtype: 'HTML',
                                        fieldname: 'message',
                                        options: `<div class="alert alert-warning">${msg}</div>`
                                    },
                                    {
                                        fieldtype: 'HTML',
                                        fieldname: 'list',
                                        options: `<ul style="max-height: 200px; overflow-y: auto;">${list}</ul>`
                                    },
                                    {
                                        label: __('Change Posting Date'),
                                        fieldtype: 'Date',
                                        fieldname: 'posting_date',
                                        default: frm.doc.posting_date,
                                        reqd: 1
                                    }
                                ],
                                primary_action_label: __('Update Date'),
                                primary_action: (values) => {
                                    if (values.posting_date) {
                                        frm.set_value('posting_date', values.posting_date);
                                        frm.refresh_field('posting_date');
                                    }
                                    d.hide();
                                }
                            });
                            d.show();
                        } else {
                            // Message for existing documents
                            frappe.msgprint({
                                title: __('Duplicate Warning'),
                                indicator: 'red',
                                message: `${msg}<ul>${list}</ul>`,
                                as_html: true,
                                alert: true
                            });
                        }
                    }
                }
            }
        });
    },
}*/