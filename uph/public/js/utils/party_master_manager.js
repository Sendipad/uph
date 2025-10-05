frappe.ui.form.PartyMasterQuickEntryForm = class PartyMasterQuickEntryForm extends (
	frappe.ui.form.QuickEntryForm
) {
	constructor(doctype, after_insert, init_callback, doc, force) {
		super(doctype, after_insert, init_callback, doc, force);
		this.skip_redirect_on_error = true;
	}

	// Helper to fetch the next party number
	fetch_next_party_number() {
		const parent = this.dialog.doc.parent_party_master;
		if (!parent) return;

		const args = { parent };
		if (this.dialog.doc.is_group) args.is_group = 1;

		frappe.call({
			method: "uph.party.doctype.party_master.party_master.get_next_party_master_number",
			args: args,
			callback: (r) => {
				if (r.message) this.dialog.set_value("party_number", r.message);
			},
		});
	}

	set_meta_and_mandatory_fields() {
		super.set_meta_and_mandatory_fields();

		this.mandatory.forEach((field) => {
			switch (field.fieldname) {
				case "party_type":
					field.fieldtype = "Link";
					field.options = "Party Type";
					field.get_query = () => ({
						filters: {
							name: ["in", Object.keys(frappe.boot.party_account_types)],
						},
					});
					field.onchange = () => {
						const type = this.dialog.doc.party_type;
						if (type === "Customer") this.dialog.set_value("group_type", "Customer Group");
						else if (type === "Supplier") this.dialog.set_value("group_type", "Supplier Group");
						else this.dialog.set_value("group_type", "");
						this.dialog.refresh_field("group_type");
					};
					field.read_only = 0;
					field.hidden = 0;
					field.description = __("This will be the Primary Role for This Party");
					break;

				case "party_name":
					field.description = __("A Unique Party Name Must be filled");
					field.onchange = () => {
						const name = this.dialog.doc.party_name;
						if (name) {
							frappe.call({
								method: "uph.party.controllers.queries.query_similar_name_or_number",
								args: { party_name: name },
								debounce: 2000,
								callback: (r) => {
									if (r.message?.exact_name) {
										const msg = `<p style="color:red"> ${__("Exists: ")} ${name} </p>`;
										this.dialog.fields_dict.party_name.df.description = msg;
									}
								},
							});
						}
					};
					break;

				case "party_number":
					field.description = __("A Unique Party Number Must Be set or leave it");
					break;

				case "parent_party_master":
				case "is_group":
					field.onchange = this.fetch_next_party_number.bind(this);
					break;
			}
		});
	}

	render_dialog() {
		this.mandatory = this.mandatory.concat(this.get_variant_fields());
		super.render_dialog();

		// fetch next party number after dialog is ready
		if (this.dialog.doc.parent_party_master) {
			this.fetch_next_party_number();
		}

		this.setup_field_listeners(); // attach onchange listeners
	}
	setup_field_listeners() {
		const d = this.dialog;

		// parent_party_master or is_group changes
		["parent_party_master", "is_group"].forEach((f) => {
			if (d.fields_dict[f]) {
				d.fields_dict[f].df.onchange = () => this.fetch_next_party_number();
			}
		});

		// party_name duplicate check
		if (d.fields_dict.party_name) {
			d.fields_dict.party_name.df.onchange = () => {
				const name = d.doc.party_name;
				if (!name) return;
				frappe.call({
					method: "uph.party.controllers.queries.query_similar_name_or_number",
					args: { party_name: name },
					debounce: 2000,
					callback: (r) => {
						if (r.message?.exact_name) {
							const msg = `<p style="color:red"> ${__("Exists: ")} ${name} </p>`;
							d.fields_dict.party_name.df.description = msg;
							d.refresh_field("party_name");
						} else {
							d.fields_dict.party_name.df.description = __("A Unique Party Name Must be filled");
							d.refresh_field("party_name");
						}
					},
				});
			};
		}
	}

	insert() {
		// Map alias fields
		const map_field_names = { email_address: "email_id", mobile_number: "mobile_no" };
		Object.entries(map_field_names).forEach(([field, new_field]) => {
			this.dialog.doc[new_field] = this.dialog.doc[field];
			delete this.dialog.doc[field];
		});

		return super.insert();
	}

	get_variant_fields() {
		return [
			{ fieldtype: "Data", fieldname: "party_details", label: __("More Details") },
			{ fieldtype: "Section Break", label: __("Primary Contact Details"), collapsible: 0 },
			{ label: __("Mobile Number"), fieldname: "mobile_number", fieldtype: "Data" },
			{ fieldtype: "Column Break" },
			{ label: __("Email Id"), fieldname: "email_address", fieldtype: "Data", options: "Email" },
			{ fieldtype: "Section Break", label: __("Primary Address Details"), collapsible: 1 },
			{ label: __("Address Line 1"), fieldname: "address_line1", fieldtype: "Data" },
			{ label: __("Address Line 2"), fieldname: "address_line2", fieldtype: "Data" },
			{ label: __("ZIP Code"), fieldname: "pincode", fieldtype: "Data" },
			{ fieldtype: "Column Break" },
			{ label: __("City"), fieldname: "city", fieldtype: "Data" },
			{ label: __("State"), fieldname: "state", fieldtype: "Data" },
			{ label: __("Country"), fieldname: "country", fieldtype: "Link", options: "Country" },
			{ label: __("Customer POS Id"), fieldname: "customer_pos_id", fieldtype: "Data", hidden: 1 },
		];
	}
};
