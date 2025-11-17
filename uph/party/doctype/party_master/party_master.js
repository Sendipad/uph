frappe.ui.form.on("Party Master", {
	setup(frm) {
		frm.set_query("roles", () => ({
			filters: {
				name: ["!=", frm.doc.party_type],
			},
		}));
	},

	onload(frm) {
		frm.set_query("roles", () => ({
			filters: {
				name: ["!=", frm.doc.party_type],
			},
		}));
	},

	is_group(frm) {
		if (!frm.doc.parent_party_master && !frm.doc.is_group) return;
		frappe.call({
			method: "uph.party.doctype.party_master.party_master.get_next_party_master_number",
			args: {
				parent: frm.doc.parent_party_master,
				is_group: frm.doc.is_group ? 1 : 0,
			},
			callback: (r) => {
				if (r.message) frm.set_value("party_number", r.message);
			},
		});
	},

	parent_party_master(frm) {
		if (!frm.doc.parent_party_master) return;

		frm.toggle_display("party_number", !frm.is_new());
		frm.refresh_field("party_number");

		const args = {
			parent: frm.doc.parent_party_master,
			...(frm.doc.is_group && { is_group: 1 }),
		};

		frappe.call({
			method: "uph.party.doctype.party_master.party_master.get_next_party_master_number",
			args,
			debounce: 100,
			callback: (r) => {
				if (r.message) {
					frm.set_value("party_number", r.message);
				}
			},
		});
	},

	refresh(frm) {
		if (frm.doc.is_group) {
			frm.dashboard.hide();
		} else {
			frm.dashboard.show();
		}

		frm.old_parent = frm.doc.parent_party_master || null;

		if (!frm.is_new()) {
			frm.set_df_property("parent_party_master", "read_only", 1);
			frm.set_df_property("party_number", "read_only", 1);

			frm.add_custom_button(
				__("Create Party"),
				() => {
					uph.party.create_party_for_party_master_dialog(frm);
				},
				__("Action")
			);
frm.add_custom_button( __("Add Secondary Roles"), () => { open_secondary_roles_dialog(frm); }, __("Action"), );
			frm.add_custom_button(
				__("Account Statement"),
				() => {
					frappe.route_options = { party_master: frm.doc.name };
					frappe.set_route("query-report", "Party Account Statement");
				},
				__("View")
			);

			frm.add_custom_button(
				__("Parties"),
				() => show_linked_parties(frm),
				__("View")
			);
if (frm.doc.total_linked_party && frm.doc.total_linked_party > 0) {
    frm.add_custom_button(
        __("Reassign Linked Parties"),
        () => build_parties_dialog(frm, "to_reassign"),
        __("Action")
    );
}

		}

		update_buttons(frm);

		frm.set_query("default_customer", () => ({
			filters: { party_master: frm.doc.name },
		}));

		frm.set_query("default_supplier", () => ({
			filters: { party_master: frm.doc.name },
		}));

		frm.toggle_display("roles", frm.doc.has_secondary_role_party === 1);
	},
	
});

// ---------------------- Utility Functions ----------------------
function build_parties_dialog(frm, action) {
    const child_table = get_child_table();
    const parties_dialog_fields = [
        { label: __("Parties"), fieldname: "parties", fieldtype: "Table", read_only: 1, fields: child_table, cannot_add_rows: true },
    ];

    const filters = [];
    if (action === "to_assign") {
        filters.push(["party_master", "is", "not set"]);
    } else if (action === "to_reassign") {
        parties_dialog_fields.push({
            label: __("To Party Master"),
            fieldname: "to_party_master",
            fieldtype: "Link",
            options: "Party Master",
            reqd: 1,
        });
        filters.push(["party_master", "=", frm.doc.name]);
    }

    frm.call({
        doc: frm.doc,
        method: "fetch_parties_list",
        args: { filters },
        callback: (r) => {
            if (!r.message) return;

            parties_dialog_fields[0].data = r.message;
            parties_dialog_fields[0].get_data = () => r.message;

            const d = new frappe.ui.Dialog({
                title: __("Parties Allocations"),
                fields: parties_dialog_fields,
                size: "large",
                primary_action_label: "Linking Parties",
                primary_action(values) {
                    const selections = values.parties.filter((x) => x.__checked);
                    if (!selections.length) {
                        frappe.msgprint(__("No Selection"));
                        return;
                    }

                    const new_party_master = action === "to_reassign" ? values.to_party_master : frm.doc.name;
                    const selection_map = selections.map((elem) => ({
                        new_party_master,
                        party_type: elem.party_type,
                        party: elem.party,
                    }));

                    frm.call({
                        doc: frm.doc,
                        method: "assign_new_party_master_for_parties",
                        args: { selections: selection_map },
                        callback: (r) => {
                            if (!r.exc) {
                                frappe.msgprint(__("Parties successfully linked!"));
                                d.hide();
                                frm.reload_doc();
                            } else {
                                frappe.msgprint(__("Something went wrong. Please check console."));
                                console.error(r.exc);
                            }
                        },
                    });
                },
            });
            d.show();
        },
    });
}

function update_buttons(frm) {
	const counts = get_counts_unlinked_parties();

	if (!counts) return;

	let party_count = counts[frm.doc.party_type] || 0;

	// Primary action: Linking existing parties
	if (party_count > 0) {
		frm.page.set_primary_action(
			__("Linking Existing {0} ({1})", [frm.doc.party_type, party_count]),
			() => fetch_existing_parties(frm, { party_type: frm.doc.party_type })
		);
	}

	// Secondary roles
	if (frm.doc.has_secondary_role_party && frm.doc.roles) {
		frm.doc.roles.forEach((role) => {
			const role_count = counts[role.party_type_role] || 0;
			if (role_count > 0) {
				frm.add_custom_button(
					__("Linking Existing {0} ({1})", [role.party_type_role, role_count]),
					() => fetch_existing_parties(frm, { party_type: role.party_type_role }),
					__("Fetch From :")
				);
			}
		});
	}
}

function fetch_existing_parties(frm, filters) {
	const dialog = new frappe.ui.form.MultiSelectDialog({
		doctype: frm.doc.doctype,
		target: frm,
		setters: { party_type: filters.party_type },
		add_filters_group: 1,
		get_query() {
			return {
				query: "uph.party.doctype.party_master.party_master.get_unset_parties_list",
				filters: { party_master: frm.doc.name, unset: 1, party_type: filters.party_type },
			};
		},
		action(selections) {
			const data = selections.map((name) => ({ name, party_type: filters.party_type }));
			frappe.call({
				method: "set_party_master",
				doc: frm.doc,
				args: { data },
				callback() {
					frm.refresh_field("linked_party");
					dialog.dialog.hide();
				},
			});
		},
	});
}

function get_counts_unlinked_parties() {
	if (frappe.boot.unlinked_parties_counts) return frappe.boot.unlinked_parties_counts;

	frappe.call({
		method: "uph.party.doctype.party_master.party_master.get_totals_number_unlinked_parties",
		async: false,
		callback(r) {
			if (r.message) frappe.boot.unlinked_parties_counts = r.message;
		},
	});

	return frappe.boot.unlinked_parties_counts || {};
}

function show_linked_parties(frm) {
	const child_table = get_child_table();

	const fields = [
		{ label: __("Parties"), fieldname: "parties", fieldtype: "Table", read_only: 1, editable: false, fields: child_table, cannot_add_rows: true }
	];

	frappe.call({
		method: "uph.party.controllers.queries.get_party_master_parties",
		args: { party_master: frm.doc.name },
		callback(r) {
			if (r.message) {
				fields[0].data = r.message;
				fields[0].get_data = () => r.message;
				new frappe.ui.Dialog({ title: __("Parties"), fields, size: "large" }).show();
			}
		},
	});
}

function get_child_table() {
	return [
		{ label: __("Party"), fieldname: "party", fieldtype: "Dynamic Link", options: "party_type", in_list_view: 1, read_only: 1 },
		{ label: __("Name"), fieldname: "party_name", fieldtype: "Data", in_list_view: 1, read_only: 1 },
		{ label: __("Party Type"), fieldname: "party_type", fieldtype: "Link", options: "DocType", in_list_view: 1, read_only: 1 },
		{ label: __("Currency"), fieldname: "currency", fieldtype: "Link", in_list_view: 1, read_only: 1 }
	];
}


function open_secondary_roles_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Add Party Roles"),
		fields: [
			{
				label: __("Activate Multi Roles"),
				fieldname: "has_secondary_role_party",
				fieldtype: "Check",
				reqd: 1,
				default: 1,
				read_only: 1,
				description: __("Activate a single party can play multiple roles customer, supplier, employee using the same base party data")
			},
			{
				label: __("Roles"),
				fieldname: "roles",
				fieldtype: "Table MultiSelect",
				options: "Party Master Role",
				reqd: 1,
				get_data(txt) {
					let existing = [frm.doc.party_type];
					if (frm.doc.roles) existing = existing.concat(frm.doc.roles.map(r => r.party_type_role));
					return frappe.db.get_list("Party Master Role", {
						fields: ["name"],
						filters: [["name", "not in", existing], ["name", "like", `%${txt}%`]],
						limit: 20
					});
				}
			}
		],
		size: "small",
		primary_action_label: __("Add"),
		primary_action(values) {
			if (!values.roles || !values.roles.length) {
				frappe.msgprint(__("Please select at least one role."));
				return;
			}

			// mark multi-role active
			frm.set_value("has_secondary_role_party", 1);

			// Convert Table MultiSelect results into proper child table format
			// Clear existing roles array if needed
			if (!frm.doc.roles) frm.doc.roles = [];

			const existing_roles = frm.doc.roles.map(r => r.party_type_role);
			values.roles.forEach(role_doc => {
				if (!existing_roles.includes(role_doc.name)) {
					frm.doc.roles.push({ party_type_role: role_doc.name });
				}
			});

			frm.refresh_field("roles");

			// Save document
			frm.save()
				.then(() => {
					dialog.hide();
					frm.reload_doc();
					frappe.show_alert({ message: __("Secondary roles added and form saved"), indicator: "green" });
				})
				.catch(err => {
					frappe.msgprint(__("Error saving form. Check console."));
					console.error(err);
				});
		}
	});

	dialog.show();
}
