if (typeof frappe !== 'undefined') {
	frappe.provide("uph");
}
window.uph = window.uph || {};
uph.party_type_pm_rules = uph.party_type_pm_rules || {};
uph.get_party_type_party_master_rules = function (party_type, callback) {
	if (!uph.party_type_pm_rules) uph.party_type_pm_rules = {};
	if (Object.keys(uph.party_type_pm_rules).length === 0) {
		frappe.call({
			method:
				"uph.party.doctype.party_master_settings.party_master_settings.get_party_type_party_master_rules_dict",
			callback: function (r) {
				if (r.message) {
					Object.assign(uph.party_type_pm_rules, r.message);
					callback(uph.party_type_pm_rules[party_type]);
				} else {
					callback(null);
				}
			},
		});
	} else {
		callback(uph.party_type_pm_rules[party_type]);
	}
}

$(document).on("app_ready", function () {
	if (!frappe.boot) return;
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
				uph.get_party_type_party_master_rules(frm.doc.doctype, function (rules) {
					if (rules) {
						frm.set_df_property("party_master", "reqd", rules.reqd);
						frm.toggle_display("is_default_for_party_master", rules.allowed);
						frm.allowed_set_default = rules.allowed;
					}
				});
			},
			refresh: function (frm) {
				if (!frm.is_new()) {
					frm.toggle_enable("party_master", !frm.doc.party_master);
					uph.get_party_type_party_master_rules(frm.doc.doctype, function (rules) {
						if (frm.doc.party_master && rules?.allowed) {
							frm.add_custom_button(
								__("Reset As Default for Party Master"),
								function () {
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
											if (!r.exc) {
												frm.refresh();
											}
										},
									});
								},
								__("Actions"),
							);
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
									get_query() {
										return {
											query: "uph.party.controllers.queries.get_party_master",
											filters: { party_type: frm.doc.doctype },
										};
									},
								},
							],
							primary_action_label: __("Link"),
							freeze: true,
							primary_action(values) {
								if (!values.party_master) return;
								frm.set_value("party_master", values.party_master);
								d.hide();
								frm.save().then(() => frm.reload_doc());
							},
						});

						// 🧩 Secondary action — Create a new Party Master (Quick Entry)
						d.set_secondary_action_label(__("Create New Party Master"));
						d.set_secondary_action(() => {
							d.hide(); // close first dialog

							// add small delay to allow backdrop to be removed
							setTimeout(() => {
								const party_name_map = {
									Customer: frm.doc.customer_name,
									Supplier: frm.doc.supplier_name,
									Employee: frm.doc.employee_name,
								};

								const party_name = party_name_map[frm.doc.doctype] || frm.doc.title || frm.doc.name;

								frappe.ui.form.make_quick_entry(
									"Party Master",
									(doc) => {
										if (doc && doc.name) {
											frm.set_value("party_master", doc.name);
											frm.save().then(() => frm.reload_doc());
											frappe.show_alert({
												message: __("Linked new Party Master {0}", [doc.party_name]),
												indicator: "green",
											});
										}
									},
									null,
									{
										party_name: party_name,
										party_type: frm.doc.doctype,
									},
									null,
									frappe.ui.form.PartyMasterQuickEntryForm,
								);
							}, 300); // small wait so modal backdrop clears
						});

						d.show();
					});
				} else if (!frm.is_new()) {
					frm.add_custom_button(__("Parent Party: {0}", [frm.doc.party_master]), function () {
						frappe.set_route("Form", "Party Master", frm.doc.party_master);
					});
					frm.add_custom_button(
						__("Unlink Party Master"),
						function () {
							frappe.confirm(__("Are you sure you want to unlink this Party Master?"), function () {
								frm.set_value("party_master", "");
								frm.save();
								frm.reload();
							});
						},
						__("Actions"),
					);
					frm.add_custom_button(
						__("Sync Party Master Details"),
						function () {
							frappe.confirm(
								__(
									"This will synchronize all details from Party Master as configured in settings. Continue?",
								),
								function () {
									let args = {
										source_name: frm.doc.party_master,
										target_doctype: frm.doc.doctype,
										target_doc: frm.doc.name,
										save: true,
									};
									frappe.call({
										method:
											"uph.party.doctype.party_master.party_master.create_party_from_party_master", // Replace with actual method path
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
												indicator: "red",
											});
										},
									});
								},
							);
						},
						__("Actions"),
					);
				}
			},
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
	if (!frappe.boot || !frappe.boot.party_master_on_doctypes_depend_field) return;
	let doctypes = frappe.boot.party_master_on_doctypes_depend_field;
	$.each(doctypes, function (i, row) {
		if (!row) return;
		let [doctype, child, fieldname] = row;
		if (doctype === child) {
			(function (doctype, fieldname) {
				frappe.ui.form.on(doctype, {
					setup: function (frm) {
						uph.party.setups(frm);
					},
					party_master: function (frm) {
						uph.party.handle_party_master_change(frm, fieldname);
						uph.party.set_party_query(frm, fieldname);
					},
					posting_date: function (frm) {
						if (!frm.fields_dict["posting_date"] || !frm.doc?.posting_date) return;
						uph.party.check_duplicate_voucher_for_party_master(frm);
					},
					refresh: function (frm) {
						uph.party.refresh(frm);
					},
				});
			})(doctype, fieldname);
		} else if (doctype !== child && fieldname) {
			(function (doctype, child, fieldname) {
				frappe.ui.form.on(doctype, {
					setup: function (frm) {
						uph.party.setup_queries_on_child(frm, child, fieldname);
					},

					posting_date: function (frm) {
						if (!frm.fields_dict["posting_date"] || !frm.doc?.posting_date) return;
						uph.party.check_duplicate_voucher_for_party_master(frm);
					},
				});
				frappe.ui.form.on(child, {
					party_master: function (frm, cdt, cdn) {
						let row = locals[cdt][cdn];
						uph.party.handle_party_master_change_in_child(frm, row);
					},
				});
			})(doctype, child, fieldname);
		}
	});
});
frappe.provide("uph.utils");

uph.utils.open_client_script_generator_dialog = function (
	frm,
	options = {},
	additional_fields = [],
) {
	const base_fields = [
		{ fieldtype: "Section Break", label: __("Details"), collapsible: 1, collapsed: 1 },
		{
			fieldtype: "Link",
			fieldname: "document_type",
			label: __("Document Type"),
			options: "DocType",
			default: options.document_type || frm.doc.document_type || frm.doc.doctype,
		},
		{
			fieldtype: "Data",
			label: __("Method"),
			fieldname: "method",
			default: options.method,
			read_only: 1,
		},
		{ fieldtype: "Column Break" },
		{
			fieldtype: "Data",
			label: __("Job Type"),
			fieldname: "job_type",
			default: frm.doc.doctype,
			read_only: 1,
		},
		{
			fieldtype: "Data",
			label: __("Job Name"),
			fieldname: "job_name",
			default: frm.doc.name,
			read_only: 1,
		},
		{ fieldtype: "Section Break", label: __("Script Settings") },
		{
			fieldname: "trigger_event",
			label: __("Trigger Event"),
			fieldtype: "Select",
			options: "Before Insert\nBefore Submit\nOn Load",
			reqd: 1,
			default: "On Load",
		},
		{
			fieldname: "target_field",
			label: __("Target Field"),
			fieldtype: "Data",
		},
		{
			fieldname: "script_name",
			label: __("Script Name"),
			fieldtype: "Data",
		},
		{
			fieldname: "trigger_on_fields",
			label: __("Trigger on Field Change"),
			fieldtype: "Data",
			default: options.trigger_on_fields || "",
		},
		{
			fieldname: "execution_mode",
			label: __("Execution Behavior"),
			fieldtype: "Select",
			options: "set_values\nshow_dialog\nalert\nmsgprint",
			default: "set_values",
		},
		{ fieldtype: "Column Break" },
		{
			fieldtype: "Check",
			fieldname: "enable_custom_button",
			label: __("Enable Custom Button"),
			default: 1,
		},
		{
			fieldtype: "Check",
			fieldname: "run_on_not_saved",
			label: __("Trigger on Unsaved Doc"),
		},
		{
			fieldtype: "Check",
			fieldname: "run_on_after_save",
			label: __("Trigger After Save"),
		},
		{
			fieldtype: "Check",
			fieldname: "run_on_submitted",
			label: __("Trigger on Submitted Doc"),
		},
	];

	const dialog = new frappe.ui.Dialog({
		title: __("Client Script Generator"),
		fields: [...base_fields, ...additional_fields],
		primary_action_label: "Generate",
		size: "extra-large",
		primary_action(values) {
			dialog.hide();

			values.target_doctype = values.document_type || frm.doc.document_type;

			frappe.call({
				method: options.backend_method || "your_app.api.generate_client_script",
				args: { options: values },
				callback(r) {
					if (r.message) {
						frappe.msgprint(__("Client Script Generated!"));
						frappe.set_route("Form", "Client Script", r.message);
					}
				},
			});
		},
	});

	dialog.show();

	// 🔁 Refresh trigger_on_fields autocomplete dynamically
	uph.utils.FieldOptionHelper.load({
		documentType: cur_frm.doc.document_type,
		callback: (fields) => {
			const fieldnames = fields.map((f) => f.value);
			dialog.set_df_property("trigger_on_fields", "options", fieldnames);
		},
	});
	dialog.fields_dict.document_type.$input.on("change", () => {
		const doctype = frm.doc.document_type;
		if (!doctype) return;

		uph.utils.FieldOptionHelper.load({
			documentType: doctype,
			callback: (fields) => {
				const fieldnames = fields.map((f) => f.value);
				dialog.set_df_property("trigger_on_fields", "options", fieldnames);
				dialog.refresh_field("trigger_on_fields");
			},
		});
	});
};
