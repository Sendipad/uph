frappe.provide("frappe.ui.form");

frappe.ui.form.PartyMasterQuickEntryForm = class PartyMasterQuickEntryForm extends (
	frappe.ui.form.QuickEntryForm
) {
	constructor(doctype, after_insert, init_callback, doc, force) {
		super(doctype, after_insert, init_callback, doc, force);
		this.skip_redirect_on_error = true;
	}
	set_meta_and_mandatory_fields() {
		super.set_meta_and_mandatory_fields();
		this.mandatory.forEach((field) => {
			if (field.fieldname === "party_type") {
				field.fieldtype = "Link"; // ✅ Match the DocType
				field.options = "Party Type"; // Link to a custom DocType or use static list via get_query

				field.get_query = function () {
					return {
						filters: {
							name: ["in", Object.keys(frappe.boot.party_account_types)],
						},
					};
				};

				field.onchange = () => {
					const party_type = cur_dialog.doc.party_type;
					if (party_type === "Customer") {
						cur_dialog.set_value("group_type", "Customer Group");
					} else if (party_type === "Supplier") {
						cur_dialog.set_value("group_type", "Supplier Group");
					} else {
						cur_dialog.set_value("group_type", "");
					}
					cur_dialog.refresh_field("group_type");
				};

				field.read_only = 0; // Make sure it's editable
				field.hidden = 0;
				field.description = __("This will be the Primary Role for This Party");
			} else if (field.fieldname == "party_name") {
				field.description = __("A Unique Party Name Must be filled");
				field.onchange = () => {
					let name = cur_dialog.doc.party_name;
					if (name) {
						frappe.call({
							method: "uph.party.controllers.queries.query_similar_name_or_number",
							args: { party_name: name },
							debounce: 2000,
							callback: (r) => {
								//console.log("return result",r.message);
								if (r.message.exact_name) {
									let msg = `<p style="color:red"> ${__("Exists: ")} ${
										cur_dialog.doc.party_name
									} </p>`;
									cur_dialog.fields_dict.party_name.df.description = msg;
								}
							},
						});
					}
				};
			} else if (field.fieldname == "party_number") {
				field.description = __("A Unique Party Number Must Be set or leave it");
			} else if (field.fieldname == "parent_party_master") {
				field.onchange = () => {
					let name = cur_dialog.doc.parent_party_master;
					let value = { parent: name };
					if (cur_dialog.doc.is_group) {
						value.is_group = 1;
					}
					if (value) {
						frappe.call({
							method: "uph.party.doctype.party_master.party_master.get_next_party_master_number",
							args: value, //i want here to only include is_group if dialog.is_group field check and value be 1 else not including this  },
							debounce: 100,
							callback: (r) => {
								if (r.message) {
									cur_dialog.set_value("party_number", r.message);
								}
							},
						});
					}
				};
			}
		});
	}
	render_dialog() {
		this.mandatory = this.mandatory.concat(this.get_variant_fields());
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
				fieldtype: "Data",
				fieldname: "party_details",
				label: __("More Details"),
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
