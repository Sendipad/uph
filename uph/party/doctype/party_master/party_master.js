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
		frm.dashboard.show();

		frm.old_parent = frm.doc.parent_party_master || null;

		if (!frm.is_new()) {
			set_party_master_dashboard_indicators(frm);

			frm.set_df_property("parent_party_master", "read_only", 1);
			frm.set_df_property("party_number", "read_only", 1);

			frm.add_custom_button(
				__("Create Party"),
				() => {
					uph.party.create_party_for_party_master_dialog(frm);
				},
				__("Action")
			);
			frm.add_custom_button(
				__("Add Secondary Roles"),
				() => {
					open_secondary_roles_dialog(frm);
				},
				__("Action")
			);
			frm.add_custom_button(
				__("Account Statement"),
				() => {
					frappe.route_options = { party_master: frm.doc.name };
					frappe.set_route("query-report", "Party Account Statement");
				},
				__("View")
			);

			frm.add_custom_button(__("Parties"), () => show_linked_parties(frm), __("View"));
			if (frm.doc.total_linked_party && frm.doc.total_linked_party > 0) {
				frm.add_custom_button(
					__("Reassign Linked Parties"),
					() => build_parties_dialog(frm, "to_reassign"),
					__("Action")
				);
			}
		}

		update_buttons(frm);
		check_high_severity_issues(frm);

		frm.set_query("default_customer", () => ({
			filters: { party_master: frm.doc.name },
		}));

		frm.set_query("default_supplier", () => ({
			filters: { party_master: frm.doc.name },
		}));

		frm.set_query("default_cost_center", () => {
			const filters = { is_group: 0 };
			if (frm.doc.represents_company) {
				filters.company = frm.doc.represents_company;
			}
			return { filters };
		});

		frm.set_query("default_project", () => ({
			query: "erpnext.controllers.queries.get_project_name",
			filters: frm.doc.represents_company ? { company: frm.doc.represents_company } : {},
		}));

		frm.set_query("default_party_analytic_accounting", () => ({
			query: "uph.party.controllers.queries.get_party_analytic_accounting_filtered",
			filters: { party_master: frm.doc.name },
		}));

		frm.toggle_display("roles", frm.doc.has_secondary_role_party === 1);
		render_relationships(frm);
	},
});

function build_parties_dialog(frm, action) {
	const child_table = get_child_table();
	const parties_dialog_fields = [
		{
			label: __("Parties"),
			fieldname: "parties",
			fieldtype: "Table",
			read_only: 1,
			fields: child_table,
			cannot_add_rows: true,
		},
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

					const new_party_master =
						action === "to_reassign" ? values.to_party_master : frm.doc.name;
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

	// Primary action: Route to Data Quality Dashboard
	if (party_count > 0) {
		frm.page.set_primary_action(
			__("Unlinked Roles in Party Issue ({0})", [party_count]),
			() => {
				frappe.route_options = { party_master: frm.doc.name };
				frappe.set_route("data-quality-dashboard");
			}
		);
	}

	// Secondary roles: Also route to Data Quality Dashboard
	if (frm.doc.has_secondary_role_party && frm.doc.roles) {
		frm.doc.roles.forEach((role) => {
			const role_count = counts[role.party_type_role] || 0;
			if (role_count > 0) {
				frm.add_custom_button(
					__("Unlinked Roles in Party Issue ({0})", [role_count]),
					() => {
						frappe.route_options = { party_master: frm.doc.name };
						frappe.set_route("data-quality-dashboard");
					},
					__("Fetch From :")
				);
			}
		});
	}
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
		{
			label: __("Parties"),
			fieldname: "parties",
			fieldtype: "Table",
			read_only: 1,
			editable: false,
			fields: child_table,
			cannot_add_rows: true,
		},
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
			in_list_view: 1,
			read_only: 1,
		},
	];
}

function open_secondary_roles_dialog(frm) {
	// Get existing child table roles
	const existing_roles = frm.doc.roles ? frm.doc.roles.map((r) => r.party_type_role) : [];

	// Build available roles from frappe.boot.party_account_types
	let party_types = Object.keys(frappe.boot.party_account_types).filter(
		(p) => p !== frm.doc.primary_role && p !== frm.doc.party_type && !existing_roles.includes(p)
	);

	// Dynamically build check fields
	const check_fields = party_types.map((role_name) => ({
		label: role_name,
		fieldname: `role_${role_name.replace(/\s+/g, "_")}`,
		fieldtype: "Check",
		default: 0,
	}));

	// If no roles are available, alert the user
	if (check_fields.length === 0) {
		frappe.msgprint(__("All secondary roles are already assigned."));
		return;
	}

	// Create dialog
	const dialog = new frappe.ui.Dialog({
		title: __("Add Secondary Roles"),
		size: "small",
		fields: [
			{
				label: __("Activate Multi Roles"),
				fieldname: "has_secondary_role_party",
				fieldtype: "Check",
				default: 1,
				read_only: 1,
			},
			...check_fields,
		],
		primary_action_label: __("Add"),
		primary_action(values) {
			// Collect checked roles
			const selected_roles = check_fields
				.filter((f) => values[f.fieldname])
				.map((f) => f.label);

			if (!selected_roles.length) {
				frappe.msgprint(__("Please select at least one role."));
				return;
			}

			// Ensure child table exists
			frm.doc.roles = frm.doc.roles || [];

			// Add selected roles to child table
			selected_roles.forEach((role_name) => {
				if (!frm.doc.roles.some((r) => r.party_type_role === role_name)) {
					const row = frappe.model.add_child(frm.doc, "Party Master Role", "roles");
					row.party_type_role = role_name; // mandatory field
				}
			});

			// Refresh child table and save
			frm.refresh_field("roles");

			frm.save()
				.then(() => {
					dialog.hide();
					frm.reload_doc();
					frappe.show_alert({
						message: __("Secondary roles added successfully"),
						indicator: "green",
					});
				})
				.catch((err) => {
					frappe.msgprint(__("Error saving form. Check console."));
					console.error(err);
				});
		},
	});

	dialog.show();
}

function set_party_master_dashboard_indicators(frm) {
	if (frm.doc.__onload && frm.doc.__onload.dashboard_info) {
		const dashboard_info = frm.doc.__onload.dashboard_info;
		// Standard Frappe dashboard refresh handles clearing

		if (dashboard_info.length > 0) {
			dashboard_info.forEach((info) => {
				const color =
					info.total_unpaid > 0 ? "orange" : info.total_unpaid < 0 ? "red" : "green";
				const unpaid_label =
					info.total_unpaid > 0
						? __("Net Receivable: {0}", [
								format_currency(info.total_unpaid, info.currency),
						  ])
						: info.total_unpaid < 0
						? __("Net Payable: {0}", [
								format_currency(Math.abs(info.total_unpaid), info.currency),
						  ])
						: __("No Outstanding Balance");

				// Add company/currency context if multi-company
				const prefix =
					dashboard_info.length > 1 ? `${info.company} (${info.currency}): ` : "";

				if (info.annual_sales) {
					frm.dashboard.add_indicator(
						`${prefix}${__("Annual Sales: {0}", [
							format_currency(info.annual_sales, info.currency),
						])}`,
						"blue"
					);
				}
				if (info.annual_purchases) {
					frm.dashboard.add_indicator(
						`${prefix}${__("Annual Purchases: {0}", [
							format_currency(info.annual_purchases, info.currency),
						])}`,
						"blue"
					);
				}

				frm.dashboard.add_indicator(`${prefix}${unpaid_label}`, color);

				if (info.unpaid_count) {
					frm.dashboard.add_indicator(
						`${prefix}${__("Total Unpaid Invoices: {0}", [info.unpaid_count])}`,
						info.unpaid_count > 0 ? "orange" : "green"
					);
				}
			});
		}
	}
}

function render_relationships(frm) {
	if (frm.is_new()) return;

	frappe.call({
		method: "uph.party.doctype.party_relationship.party_relationship.get_party_relationships",
		args: {
			party_master: frm.doc.name,
		},
		callback: function (r) {
			if (!r.message || r.message.length === 0) {
				frm.fields_dict.relationships_html.$wrapper.html(
					'<div class="text-muted">' + __("No relationships found") + "</div>"
				);
				return;
			}

			let relationships = r.message;
			let html = `
                <table class="table table-bordered table-sm">
                    <thead>
                        <tr>
                            <th>${__("Relationship")}</th>
                            <th>${__("Related Party")}</th>
                            <th>${__("Status")}</th>
                            <th>${__("Ownership %")}</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

			relationships.forEach((rel) => {
				let related_party =
					rel.subject_party === frm.doc.name ? rel.object_party : rel.subject_party;
				let direction = rel.subject_party === frm.doc.name ? __("Is") : __("Has");
				// e.g. Subject(Me) IS Parent of Object. OR Subject(Parent) HAS Subsidiary(Me).
				// Actually, the relationship type name handles this better usually.
				// But let's just show raw type and related party.

				let rel_label = rel.relationship_type;
				if (rel.subject_party === frm.doc.name) {
					rel_label = `${rel_label} ->`;
				} else {
					rel_label = `<- ${rel_label}`;
				}

				html += `
                    <tr>
                        <td>
                            <a href="/app/party-relationship/${
								rel.name
							}" data-doctype="Party Relationship" data-name="${rel.name}">
                                ${rel_label}
                            </a>
                        </td>
                        <td>
                            <a href="/app/party-master/${related_party}" data-doctype="Party Master" data-name="${related_party}">
                                ${related_party}
                            </a>
                        </td>
                        <td>${rel.status}</td>
                        <td>${rel.ownership_percentage ? rel.ownership_percentage + "%" : "-"}</td>
                    </tr>
                `;
			});

			html += "</tbody></table>";

			// Add a button to create new relationship
			html += `
                <div class="mt-2">
                    <button class="btn btn-sm btn-default" onclick="frappe.new_doc('Party Relationship', {subject_party: '${
						frm.doc.name
					}'})">
                        ${__("Add Relationship")}
                    </button>
                </div>
            `;

			frm.fields_dict.relationships_html.$wrapper.html(html);
		},
	});
}

function check_high_severity_issues(frm) {
	if (frm.is_new()) return;

	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Party Issue",
			filters: {
				party_master: frm.doc.name,
				status: ["in", ["Open", "Under Review"]],
				severity: ["in", ["High", "Critical"]],
			},
		},
		callback: (r) => {
			if (r.message && r.message > 0) {
				frm.dashboard.set_headline(
					__("This Party Master has {0} high severity issues that require attention.", [
						r.message,
					]),
					"red"
				);
			}
		},
	});
}
