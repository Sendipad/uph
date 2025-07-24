frappe.listview_settings["Rule"] = {
	primary_action: function () {
		this.new_rule_dialog();
	},

	new_rule_dialog() {
		if (
			!(
				frappe.session.user === "Administrator" || frappe.boot.user.roles.includes("System Manager")
			)
		) {
			frappe.msgprint(__("You are not allowed to create New Rule"));
		}
		let apply_scope = [];
		let fields = [
			{
				label: __("Name"),
				fieldname: "title",
				fieldtype: "Data",
				reqd: 1,
			},
			{ fieldtype: "Column Break" },
			{
				label: __("Rule Service Type"),
				fieldname: "rule_service_type",
				fieldtype: "Link",
				options: "Rule Service Type",
				reqd: 1,
			},
			{
				fieldtype: "Section Break",
				description: __("You can apply a Rule on Single Doctype or a Multi Different DocType"),
			},
			{
				label: __("Apply on Document Type"),
				fieldname: "document_type",
				fieldtype: "Link",
				options: "DocType",
				get_query: function () {
					return {
						filters: {
							issingle: 0,
							istable: 0,
						},
					};
				},
				onchange: () => {
					let dt = cur_dialog.get_value("document_type");
					if (dt) {
						apply_scope.push({ document_type: dt, evaluation_event: "Before Save" });
						cur_dialog.fields_dict.apply_scopes.refresh();
					}
				},
			},
			{
				label: __("Apply Scope"),
				fieldname: "apply_scopes",
				fieldtype: "Table",
				//data: apply_scope,
				get_data: () => apply_scope,
				fields: [
					{
						label: __("Document Type"),
						fieldname: "document_type",
						in_list_view: 1,
						fieldtype: "Link",
						options: "DocType",
						//default: new_r.get_value("document_type"),
						reqd: 1,

						get_query: function () {
							return {
								filters: {
									issingle: 0,
									istable: 0,
								},
							};
						},
					},

					{
						label: __("Triggered On"),
						fieldname: "evaluation_event",
						in_list_view: 1,
						fieldtype: "Select",
						options: "Before Save",
						reqd: 1,

						default: "Before Save",
					},
				],
			},
		];

		let new_r = new frappe.ui.Dialog({
			title: __("Create New Rule"),
			fields: fields,
			primary_action_label: __("Create & Continue"),
			primary_action(values) {
				if (!values.istable) values.editable_grid = 0;
				frappe.db
					.insert({
						doctype: "Rule",
						...values,
					})
					.then((doc) => {
						frappe.set_route("Form", "Rule", doc.name);
					});
			},
			secondary_action_label: __("Cancel"),
			secondary_action() {
				new_r.hide();
				if (frappe.get_route()[0] === "Form") {
					frappe.set_route("List", "Rule");
				}
			},
		});
		new_r.show();
	},
};
