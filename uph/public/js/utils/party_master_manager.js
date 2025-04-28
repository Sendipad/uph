
frappe.provide("frappe.ui.form");
frappe.ui.form.PartyMasterQuickEntryForm = class PartyMasterQuickEntryForm extends (
	frappe.ui.form.QuickEntryForm
){
	constructor(doctype, after_insert, init_callback, doc, force) {
		super(doctype, after_insert, init_callback, doc, force);
		this.skip_redirect_on_error = true;
	}
  set_meta_and_mandatory_fields(){
    super.set_meta_and_mandatory_fields();
    this.mandatory.forEach(field=>{
      if(field.fieldname=='party_type'){
        field.fieldtype="Select";
        field.options=Object.keys(frappe.boot.party_account_types);
        field.onchange=()=>{
          let party_type=cur_dialog.doc.party_type;
          if (party_type=='Customer'){
            cur_dialog.set_value("group_type","Customer Group");
          }else if(party_type=='Supplier'){
            cur_dialog.set_value("group_type","Supplier Group");
        }else{
          cur_dialog.set_value("group_type","");

        }
        cur_dialog.refresh_field("group_type");
      }
        field.description=__("This will be the Primary Role for This Party");
      }else if(field.fieldname=="party_name"){
        field.description=__("A Unique Party Name Must be filled");
        field.onchange=()=>{
          let name=cur_dialog.doc.party_name;
          if (name){
            frappe.call({
              method: 'uph.party.controllers.queries.query_similar_name_or_number',
              args: { party_name: name },
              debounce:2000,
              callback: (r) => {
                //console.log("return result",r.message);
                  if (r.message.exact_name) {
                    let msg=`<p style="color:red"> ${__("Exists: ")} ${cur_dialog.doc.party_name} </p>`
                    cur_dialog.fields_dict.party_name.df.description=msg;

                 
                  }
              }
          });
          }
        }
      }else if(field.fieldname=="party_number"){
        field.description=__("A Unique Party Number Must Be set or leave it")
      }else if(field.fieldname=="parent_party_master"){
        field.onchange=()=>{
          let name=cur_dialog.doc.parent_party_master;
          let value={parent:name};
          if(cur_dialog.doc.is_group){
            value.is_group=1;
          }
          if (value){
            frappe.call({
              method: 'uph.party.doctype.party_master.party_master.get_next_party_master_number',
              args: value, //i want here to only include is_group if dialog.is_group field check and value be 1 else not including this  },
              debounce:100,
              callback: (r) => {
                  if (r.message) {
                    cur_dialog.set_value("party_number",r.message);

                 
                  }
              }
          });
          }
        }
      }
    });
  }
	render_dialog() {
		
    this.mandatory=this.mandatory.concat(this.get_variant_fields());
		super.render_dialog();
	}

	insert() {
		/**
		 * Using alias fieldnames because the doctype definition define "email_id" and "mobile_no" as readonly fields.
		 * Therefor, resulting in the fields being "hidden".
		 */
		const map_field_names = {
			email_address: "email_id",
			mobile_number: "mobile_no",
		};

		Object.entries(map_field_names).forEach(([fieldname, new_fieldname]) => {
			this.dialog.doc[new_fieldname] = this.dialog.doc[fieldname];
			delete this.dialog.doc[fieldname];
		});

		return super.insert();
	}

	get_variant_fields() {
		var variant_fields = [
      {
        fieldtype:"Data",
        fieldname:"party_details",
        label:__("More Details"),
      },
			{
				fieldtype: "Section Break",
				label: __("Primary Contact Details"),
				collapsible: 0,
			},
    
      {
				label: __("Mobile Number"),
				fieldname: "mobile_number",
				fieldtype: "Data",
			},
			
			{
				fieldtype: "Column Break",
			},
      {
				label: __("Email Id"),
				fieldname: "email_address",
				fieldtype: "Data",
				options: "Email",
			},
	
      
      {
				fieldtype: "Section Break",
				label: __("Primary Address Details"),
				collapsible: 1,
			},
			{
				label: __("Address Line 1"),
				fieldname: "address_line1",
				fieldtype: "Data",
			},
			{
				label: __("Address Line 2"),
				fieldname: "address_line2",
				fieldtype: "Data",
			},
			{
				label: __("ZIP Code"),
				fieldname: "pincode",
				fieldtype: "Data",
			},
			{
				fieldtype: "Column Break",
			},
			{
				label: __("City"),
				fieldname: "city",
				fieldtype: "Data",
			},
			{
				label: __("State"),
				fieldname: "state",
				fieldtype: "Data",
			},
			{
				label: __("Country"),
				fieldname: "country",
				fieldtype: "Link",
				options: "Country",
			},
			{
				label: __("Customer POS Id"),
				fieldname: "customer_pos_id",
				fieldtype: "Data",
				hidden: 1,
			},
		];

		return variant_fields;
	}
};
/*
frappe.provide("uph.party_master");
uph.party_master = {
  get_fields: function (frm) {
    const meta = frappe.get_meta(frm.doctype);
    return meta.fields
      .filter(
        (df) =>
          (df.reqd || df.allow_in_quick_entry) &&
          !df.read_only &&
          !df.is_virtual &&
          !["Tab Break", "Column Break", "Section Break"].includes(df.fieldtype)
      )
      .map((df) => ({
        fieldtype: df.fieldtype,
        fieldname: df.fieldname,
        label: df.label,
        options: df.options,
        reqd: df.reqd,
        description: df.description,
      }));
  },

  ovride_fields: function(frm) {
    let fields = this.get_fields(frm);
    
    // Modify party_type field
    fields = fields.map(df => {
        if (df.fieldname === 'party_type') {
            return {
                ...df,
                fieldtype: 'Select',
                options: Object.keys(frappe.boot.party_account_types || {}),
                default: 'Customer',
                description: __('Select a primary Role type of party')
            };
        }
        return df;
    });
    fields = fields.map(df => {
      if (df.fieldname === 'party_number') {
          return {
              ...df,
              description: __('Set a unique party number if It is not Group leave it'),
              on_change: (value) => this.handle_party_name_change(value, frm)
          };
      }
      return df;
  });
    // Add on_change property to party_name
    fields = fields.map(df => {
        if (df.fieldname === 'party_name') {
            return {
                ...df,
                on_change: (value) => this.handle_party_name_change(value, frm)
            };
        }
        return df;
    });

    return fields;
},

handle_party_name_change: function(value, frm) {
    if (!value) return;

    frappe.call({
        method: 'uph.party.controllers.party.check_similar_party_name',
        args: { party_name: value },
        callback: (r) => {
            if (r.message.exists) {
                frappe.msgprint({
                    title: __('Duplicate Found'),
                    indicator: 'orange',
                    message: __('Similar party already exists: {0}', [r.message.similar_name])
                });
            }
        }
    });
},

quick_entry: function(frm, predefined_data = {}) {
  const fields = this.ovride_fields(frm);
  const dialog = new frappe.ui.Dialog({
      title: __('Quick Create Party'),
      fields: fields,
      size:'xtra-large',
      primary_action: values => {
        dialog.disable_primary_action();

        // Create new party doc
        const doc = {
          doctype: frm.doctype,
          ...values,
        };

        frappe.db
          .insert(doc)
          .then((new_doc) => {
            dialog.hide();
            frappe.show_alert(
              {
                message: __("{0} created successfully", [new_doc.name]),
                indicator: "green",
              },
              5
            );

            // Refresh form if open
            if (cur_frm && cur_frm.doctype === frm.doctype) {
              cur_frm.reload_doc();
            }
          })
          .catch((err) => {
            frappe.msgprint({
              title: __("Error"),
              indicator: "red",
              message: __("Could not create party: {0}", [err.message]),
            });
          })
          .finally(() => {
            dialog.enable_primary_action();
          });
      },
    });

    // Add custom styling
    dialog.$wrapper.addClass("party-quick-entry-dialog");

    // Show mandatory fields first
    dialog.fields_list.forEach((field) => {
      if (field.df.reqd) {
        field.$wrapper.addClass("reqd-field-highlight");
      }
    });
  // Set predefined values after dialog renders
  dialog.show().then(() => {
      // 1. Set field defaults from predefined_data
      Object.entries(predefined_data).forEach(([fieldname, value]) => {
          const field = dialog.get_field(fieldname);
          if (field) {
              field.set_value(value);
          }
      });

      // 2. Attach on_change handlers (existing logic)
      fields.forEach(df => {
          if (df.on_change) {
              const field = dialog.get_field(df.fieldname);
              if (field) {
                  field.$input.on('input', () => df.on_change(field.get_value()));
              }
          }
      });
  });

  return dialog;
},

};*/