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
						if (type === "Customer")
							this.dialog.set_value("group_type", "Customer Group");
						else if (type === "Supplier")
							this.dialog.set_value("group_type", "Supplier Group");
						else this.dialog.set_value("group_type", "");
						this.dialog.get_field("group_type").refresh();
					};
					field.read_only = 0;
					field.hidden = 0;
					field.description = __("This will be the Primary Role for This Party");
					break;

				case "party_name":
					field.description = __("A Unique Party Name Must be filled");
					break;

				case "party_number":
					field.description = __("A Unique Party Number Must Be set or leave it");
					break;

				case "parent_party_master":
					field.onchange = this.fetch_next_party_number.bind(this);
					break;
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

		// party_name and party_number duplicate check
		const check_duplicate = frappe.utils.debounce((fieldname, value) => {
			if (!value) return;

			frappe.call({
				method: "uph.party.controllers.queries.query_similar_name_or_number",
				args: { [fieldname]: value },
				callback: (r) => {
					const field = d.get_field(fieldname);
					if (!field) return;

					let desc = "";
					const msg = r.message || {};

					if (msg.exact_name || msg.exact_number) {
						desc = `<span style="color:red; font-weight:bold;"> ${__("Exists: ")} ${
							msg.exact_name || msg.exact_number
						} </span>`;
					} else if (msg.fuzzy_name) {
						desc = `<span style="color:orange; font-weight:bold;"> ${__("Similar: ")} ${
							msg.fuzzy_name
						} (${msg.fuzzy_score}%) </span>`;
					} else {
						desc =
							fieldname === "party_name"
								? __("A Unique Party Name Must be filled")
								: __("A Unique Party Number Must Be set or leave it");
					}

					field.set_description(desc);

					if (field.$wrapper) {
						field.$wrapper.find(".help-box").html(desc).show();
					}

					setTimeout(() => {
						if (field.$wrapper) {
							field.$wrapper.find(".help-box").html(desc).show();
						}
					}, 100);
				},
			});
		}, 500);

		["party_name", "party_number"].forEach((f) => {
			const field = d.get_field(f);
			if (field && field.$input) {
				field.$input.on("input", () => {
					check_duplicate(f, field.get_value());
				});
			}
		});
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
			{
				label: __("Email Id"),
				fieldname: "email_address",
				fieldtype: "Data",
				options: "Email",
			},
			{ fieldtype: "Section Break", label: __("Primary Address Details"), collapsible: 1 },
			{ label: __("Address Line 1"), fieldname: "address_line1", fieldtype: "Data" },
			{ label: __("Address Line 2"), fieldname: "address_line2", fieldtype: "Data" },
			{ label: __("ZIP Code"), fieldname: "pincode", fieldtype: "Data" },
			{ fieldtype: "Column Break" },
			{ label: __("City"), fieldname: "city", fieldtype: "Data" },
			{ label: __("State"), fieldname: "state", fieldtype: "Data" },
			{ label: __("Country"), fieldname: "country", fieldtype: "Link", options: "Country" },
			{
				label: __("Customer POS Id"),
				fieldname: "customer_pos_id",
				fieldtype: "Data",
				hidden: 1,
			},
		];
	}
};
