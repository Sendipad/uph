frappe.ui.form.on("Party Master", {
  setup: function (frm) {
    console.log("Setup", get_counts_unlinked_parties(frm));
   
  },
  onload: function(frm) {
    frm.set_query('roles', () => {
      return {
        filters: {
          name: ["!=",frm.doc.party_type]
        }
      };
    });
  },
    update_button(frm) {
    if (frm.is_new()) {
      return;
    }
    if (frm.doc.total_linked_party) {
      frm.add_custom_button(
        __("Reassign Linked Parties"),
        () => frm.events.build_parties_dialog(frm, "to_reassign"),
        __("Action")
      );
    }
    const count = get_counts_unlinked_parties();
    if (count[frm.doc.party_type] > 0) {
      frm.page.set_primary_action(__("Fetch Existing Parties"), () =>
        frm.events.build_parties_dialog(frm, (action = "to_assign"))
      );

      //console.log("just Started",filter);
    }
  },
 

  build_parties_dialog: function (frm, action) {
    let child_table=get_child_table();
    let parties_dialog_fields = [
      {
        label: __("Parties"),
        fieldname: "parties",
        fieldtype: "Table",
        read_only: 1,
        fields: child_table,
        cannot_add_rows: true,
      },
    ];
    let to_party_master = {
      label: __("To Party Master"),
      fieldname: "to_party_master",
      fieldtype: "Link",
      options: "Party Master",
      reqd: 1,
    };
    let filter = []; /*
    party_type=[frm.doc.party_type];*/

    if (action == "to_assign") {
      filter.push(["party_master", "is", "not set"]);
    } else if (action == "to_reassign") {
      parties_dialog_fields.push(to_party_master);
      filter.push(["party_master", "=", frm.doc.name]);
    }
    frm.call({
      doc: frm.doc,
      method: "fetch_parties_list",
      args: { filters: filter },
      callback: function (r) {
        if (r.message) {
          parties_dialog_fields[0].data = r.message;
          parties_dialog_fields[0].get_data = function () {
            return r.message;
          };
          let d = new frappe.ui.Dialog({
            title: __("Parties Allocations"),
            fields: parties_dialog_fields,
            size: "large",
            primary_action_label: "Linking Parties",
            primary_action(values) {
              let selections = values.parties.filter((x) => x.__checked);
              let selection_map = [];
              if (selections.length > 0) {
                let new_party_master =
                  action === "to_reassign"
                    ? values.to_party_master
                    : frm.doc.name;
                selection_map = [
                  ...selections.map(function (elem) {
                    return {
                      new_party_master: new_party_master,
                      party_type: elem.party_type,
                      party: elem.party,
                    };
                  }),
                ];

                let old_party_master = frm.doc.name;
                console.log(selection_map);
                frm.call({
                  doc: frm.doc,
                  method: "assign_new_party_master_for_parties",
                  args: { selections: selection_map },
                  callback: function (r) {
                    if (!r.exc) {
                      frappe.msgprint(__("Parties successfully linked!"));
                      d.hide();
                      frm.reload_doc(); // Refresh the document
                    } else {
                      frappe.msgprint(
                        __("Something went wrong. Please check console.")
                      );
                      console.error(r.exc);
                    }
                  },
                });
              } else {
                frappe.msgprint(__("No Selection"));
              }
            },
          });

          d.show();
        }
      },
    });
  },
  after_save: function (frm) {
    if (frm.doc.reference_doctype && frm.doc.reference_docname) {
        frappe.run_serially([
            () => frappe.set_route("Form", frm.doc.reference_doctype, frm.doc.reference_docname),
            () => frappe.timeout(1), // Small delay to ensure navigation completes
            () => {
                frappe.model.set_value(frm.doc.reference_doctype, frm.doc.reference_docname, "party_master", frm.doc.name);
                
                // Ensure the reference doctype is in party_account_types before saving
                if (Object.keys(frappe.boot.party_account_types).includes(frm.doc.reference_doctype)) {
                    cur_frm.save();
                }
            }
        ]);
    }
},
  refresh: function (frm) {
   
    if(!frm.is_new()){
      
        frm.add_custom_button(__('Create Party'), () => {
            // Get unique party types from doc and roles
            let party_type = [frm.doc.party_type];
            if (frm.doc.roles && frm.doc.roles.length > 0) {
                party_type = [...new Set([frm.doc.party_type, ...frm.doc.roles.map(role => role.party_type_role)])];
            }
    
            const dialog = new frappe.ui.Dialog({
                title: __("Create Party As"),
                fields: [
                    {
                        fieldname: "party_type",
                        fieldtype: "Select",
                        label: __("Select Party Type"),
                        options: party_type,
                        reqd: 1,
                        onchange: function () {
                            const selected = dialog.get_value('party_type');
                            const showCurrency = ['Customer', 'Supplier'].includes(selected);
                            dialog.set_df_property("default_currency", "hidden", !showCurrency);
                            dialog.set_df_property("default_currency", "reqd", showCurrency ? 1 : 0);
                        }
                    },
                    {
                        fieldname: "default_currency",
                        fieldtype: "Select",
                        label: __("Default Currency"),
                        options: erpnext.get_presentation_currency_list() || [],
                        //hidden: 1
                    },
                    {
                        fieldname: "save",
                        fieldtype: "Check",
                        label: __("Save"),
                        default: 0,
                        description: __("Check this if you want to save the party without routing to Edit")
                    }
                ],
                primary_action_label: __("Edit Before Save"),
                primary_action(values) {
                    const args = {
                        source_name: frm.doc.name,
                        target_doctype: values.party_type,
                        rule_field_value: values.default_currency,
                      };
                      if(values.save){
                        args.save=true;
                      }
                    console.log("args", args);
                    frappe.call({
                        method: 'uph.party.doctype.party_master.party_master.create_party_from_party_master',
                        args: args,
                        callback(r) {
                          if (!r.exc && r.message) {
                              dialog.hide();
                      
                              if (values.save) {
                                  frappe.msgprint({message:__("Party Created Successfully"), alert : true,});
                                  frm.reload_doc();
                                } else {
                                  const doc = r.message;
                      
                                  // If doc is local (not saved)
                                  if (doc.__islocal || doc.__unsaved || doc.name?.startsWith("new-")) {
                                      frappe.model.with_doctype(doc.doctype, () => {
                                          // Create a new local doc
                                          const new_doc = frappe.model.get_new_doc(doc.doctype);
                      
                                          // Assign fields from server response
                                          Object.keys(doc).forEach(key => {
                                              if (key !== 'name' && key !== 'doctype') {
                                                  new_doc[key] = doc[key];
                                              }
                                          });
                      
                                          // Set route to the new unsaved doc
                                          frappe.set_route("Form", doc.doctype, new_doc.name);
                                      });
                                  } else {
                                      // Already saved — can route directly
                                      frappe.model.sync([doc]);
                                      frappe.set_route("Form", doc.doctype, doc.name);
                                  }
                              }
                          }
                      }
                    });
                }
            });
    
            dialog.set_value("party_type", frm.doc.party_type);
           
            dialog.show();
        },__('Action'));
    
    


      frm.add_custom_button(__("Parties"),(doc)=>{
        let child_table=get_child_table();
        let parties_dialog_fields = [
          {
            label: __("Parties"),
            fieldname: "parties",
            fieldtype: "Table",
            read_only: 1,
            editable:false,
            fields: child_table,
            cannot_add_rows: true,
          },
        ];
        let party_master=cur_frm.doc.name;
        frappe.call({
          method:"uph.party.controllers.queries.get_party_master_parties",
          args:{party_master:party_master},
          callback:function(r){
            if(r.message){
              parties_dialog_fields[0].data = r.message;
              parties_dialog_fields[0].get_data = function () {
                return r.message;
              };
              let d = new frappe.ui.Dialog({
                title: __("Parties"),
                fields: parties_dialog_fields,
                size: "large",
                //primary_action_label: "Linking Parties",
               
              });
              d.show();
            }
          }
        });
      });
    }
    frm.events.update_button(frm);
    frm.set_query("default_customer", function (doc) {
      return {
        filters: { party_master: frm.doc.name },
      };
    });
    frm.set_query("default_supplier", function (doc) {
      return {
        filters: { party_master: frm.doc.name },
      };
    });

    frm.toggle_display('roles',frm.doc.has_secondary_role_party===1);
    

    
  },
});

function update_button(frm) {
  const count = get_counts_unlinked_parties();
  let button = [];
  if (count[frm.doc.party_type] > 0) {
    button.push({
      label: __("Fetch Exist{}", [frm.doc.party_type]),
      filters: {
        party_type: frm.doc.party_type,
        party_master: frm.doc.name,
      },
    });
  }
  if (frm.doc.has_secondary_role_party && frm.doc.roles.lenght > 0) {
    frm.doc.roles.forEach((element) => {
      if (count[element.party_type_role] > 0) {
        button.push({
          label: __("Fetch Exist{}", [element.party_type_role]),
          filters: {
            party_type: element.party_type,
            party_master: frm.doc.name,
          },
        });
      }
    });
    console.log("buttons:", button);
    if (button.length == 1) {
      frm.page.set_primary_action(button[0].label, function (frm) {
        fetch_exist_parties(frm, (filters = button[0].filters));
      });
    } else {
      button.forEach((b) => {
        frm.add_custom_button(
          b.label,
          function (frm) {
            fetch_exist_parties(frm, (filters = b.filters));
          },
          __("Fetch From :")
        );
      });
    }
  }
}
function fetch_exist_parties(frm, filters, method) {
  () => {
    if (!method && filters) {
      method =
        "uph.party.doctype.party_master.party_master.get_unset_parties_list";
    }
    const d = new frappe.ui.form.MultiSelectDialog({
      doctype: frm.doc.doctype,
      target: frm,
      setters: {
        party_type: filters.party_type,
      },
      add_filters_group: 1, // `columns` is removed (not supported)

      get_query() {
        return {
          query: method,
          filters: {
            party_master: frm.doc.name,
            unset: 1,
            party_type: filters.party_type,
          },
        };
      },

      action(selections) {
        console.log("Selected:", selections);

        let data = selections.map((r) => ({
          name: r, // `selections` only returns names
          party_type: filters.party_type, // Assuming `party_type` is static
        }));

        // Fetch additional fields
        frappe.call({
          method: "set_party_master",
          doc: frm.doc,
          args: { data: data }, // Corrected format
          callback: function (response) {
            console.log("Server Response:", response);

            // Refresh linked field
            frm.refresh_field("linked_party");

            // Hide dialog after operation completes
            d.dialog.hide();
          },
        });
      },
    });
  };
}
function get_counts_unlinked_parties(frm, party_type) {
  if (frappe.boot.unlinked_parties_counts) {
    console.log(frappe.boot.unlinked_parties_count);
    return frappe.boot.unlinked_parties_counts;
  } else {
    frappe.call({
      method:
        "uph.party.doctype.party_master.party_master.get_totals_number_unlinked_parties",
      filters: {},
      callback: function (response) {
        console.log("Totals Ublinked Parties:", response);
        if (response) {
          frappe.boot.unlinked_parties_counts = response["message"];
          console.log("Boot infor:", frappe.boot.unlinked_parties_counts);
        }
      },
    });
  }
}

function get_child_table(){
  return  [
    {
      label: __("Party"),
      fieldname: "party",
      fieldtype: "Dynamic Link",
      options: "party_type",
      in_list_view: 1,
      read_only: 1,
    },
    {
      label: __("Name"),
      fieldname: "party_name",
      fieldtype: "Data",
      in_list_view: 1,
      read_only: 1,
    },
    {
      label: __("Party Type"),
      fieldname: "party_type",
      fieldtype: "Link",
      options: "DocType",
      in_list_view: 1,
      read_only: 1,
    },
    {
      label: __("Currency"),
      fieldname: "currency",
      fieldtype: "Link",
      read_only: 1,
      in_list_view: 1,

    },
  ];
}