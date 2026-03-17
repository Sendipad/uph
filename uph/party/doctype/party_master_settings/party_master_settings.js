// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt
frappe.ui.form.on("Party Master Settings", {
	onload: function (frm) {
		// Prevent adding/removing rows for party_types grid
		if (frm.fields_dict["party_types"]?.grid) {
			frm.fields_dict["party_types"].grid.cannot_add_rows = true;
			frm.fields_dict["party_types"].grid.cannot_delete_rows = true;
			// Refresh with string literal
			frm.refresh_field("party_types");
		}
	},

	refresh: function (frm) {
		// Enforce Setup Wizard if not finished
		if (!frm.doc.setup_finished && frappe.user.has_role("System Manager")) {
			frappe.msgprint({
				title: __("Setup Required"),
				message: __("UPH Setup is not complete. Redirecting to Setup Wizard..."),
				indicator: "orange",
			});
			frappe.set_route("uph-setup-wizard");
			return;
		}

		// Refresh the document_types grid
		frm.refresh_field("document_types");

		// Refresh the party_types grid
		frm.refresh_field("party_types");

		// Update selection fields for existing rows in party_types
		if (frm.doc.party_types && frm.doc.party_types.length) {
			frm.doc.party_types.forEach((row) => {
				update_party_type_rule_field(frm, "Party Master Settings Party Type", row.name);
			});
		}

		// Update selection fields for existing rows
		if (frm.doc.document_types && frm.doc.document_types.length) {
			frm.doc.document_types.forEach((row) => {
				update_selection_fields(frm, "Party Master Settings DocType", row.name);
			});
		}

		// Add description to document_types grid (only once)
		let grid = frm.fields_dict.document_types?.grid;
		if (grid) {
			let wrapper = $(grid.parent);
			if (!wrapper.find(".custom-table-description").length) {
				wrapper.append(`
                    <div class="custom-table-description"
                        style="margin-top: 15px; padding: 15px; background-color: #f8f9fa; border-left: 4px solid var(--blue-500);
                               border-radius: 3px; border-top: 1px solid #dfe3e6; border-right: 1px solid #dfe3e6; border-bottom: 1px solid #dfe3e6;">
                        <h5 style="margin-bottom: 5px; color: #2e3b4a; font-weight: 600;">
                            <i class="fa fa-info-circle text-blue"></i> ${__(
								"Understanding Document Types Configuration"
							)}
                        </h5>
                        <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 10px;">
                            ${__(
								"This table defines which transactional DocTypes (like Sales Invoice or Journal Entry) the system will monitor to guarantee Data Quality and Party Master validation."
							)}
                        </p>
                        <h6 style="margin-bottom: 5px; color: #36414c; font-size: 13px; font-weight: 600;">${__(
							"What you should set:"
						)}</h6>
                        <ul style="color: #4a5660; list-style: disc; padding-left: 25px; font-size: 12px; margin-bottom: 10px;">
                            <li><b>${__("Document Type")}</b>: ${__(
					"The exact voucher or child table to validate (e.g., Sales Invoice)."
				)}</li>
                            <li><b>${__("Parent Doctype")}</b>: ${__(
					"If you add a Child Table (e.g., Journal Entry Account), select its Parent (e.g., Journal Entry)."
				)}</li>
                            <li><b>${__("Party Fieldname")}</b>: ${__(
					"The field connecting to the Party (e.g., customer, party, supplier)."
				)}</li>
                            <li><b>${__("Party Type Fieldname")}</b>: ${__(
					"Required if the Party Field is dynamic (e.g., party_type)."
				)}</li>
                        </ul>
                        <h6 style="margin-bottom: 5px; color: #36414c; font-size: 13px; font-weight: 600;">${__(
							"How it affects the system:"
						)}</h6>
                        <ul style="color: #4a5660; list-style: disc; padding-left: 25px; font-size: 12px; margin-bottom: 0;">
                            <li>${__(
								"<b>Data Quality Dashboard</b>: Documents configured here will be scanned for Missing Party Masters and Transaction Policy issues."
							)}</li>
                            <li>${__(
								"<b>Validation</b>: The system will automatically link the Party Master upon saving, or block transactions if the Party is invalid or missing."
							)}</li>
                        </ul>
                    </div>
                `);
			}
		}
	},
});

frappe.ui.form.on("Party Master Settings Party Type", {
	form_render: function (frm, cdt, cdn) {
		update_party_type_rule_field(frm, cdt, cdn);
	},
	party_type: function (frm, cdt, cdn) {
		update_party_type_rule_field(frm, cdt, cdn);
	},
	allowed: function (frm, cdt, cdn) {
		update_party_type_rule_field(frm, cdt, cdn);
	},
	rule_fieldname: function (frm, cdt, cdn) {
		// Ensure options are there when clicking the field
		update_party_type_rule_field(frm, cdt, cdn);
	},
});

frappe.ui.form.on("Party Master Settings DocType", {
	form_render: function (frm, cdt, cdn) {
		update_selection_fields(frm, cdt, cdn);
	},

	document_type: function (frm, cdt, cdn) {
		update_selection_fields(frm, cdt, cdn);
	},
});

function update_selection_fields(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	if (!row || !row.document_type) return;

	// Defensive check: Ensure we are only acting on the correct child table
	if (cdt !== "Party Master Settings DocType") return;

	frappe.model.with_doctype(row.document_type, () => {
		let meta = frappe.get_meta(row.document_type);
		if (!meta) return;

		let fieldnames = meta.fields
			.filter((d) => !frappe.model.no_value_type.includes(d.fieldtype))
			.map((d) => d.fieldname);

		let grid = frm.fields_dict.document_types?.grid;
		if (!grid) return;

		let grid_row = grid.get_row(cdn);
		if (!grid_row || !grid_row.fields_dict) return;

		// Update field options (for Select fields)
		["party_fieldname", "party_type_fieldname"].forEach((fname) => {
			const field = grid_row.fields_dict[fname];
			if (field && field.df) {
				field.df.options = fieldnames.join("\n");
				field.refresh();
			}
		});

		// Validate existing values (and ensure field exists in child table meta)
		const row_meta = frappe.get_meta(cdt);
		if (row_meta && row_meta.fields.find((f) => f.fieldname === "party_fieldname")) {
			if (row.party_fieldname && !fieldnames.includes(row.party_fieldname)) {
				frappe.model.set_value(cdt, cdn, "party_fieldname", "");
			}
		}

		if (
			row.is_dynamic_party_type &&
			row_meta &&
			row_meta.fields.find((f) => f.fieldname === "party_type_fieldname")
		) {
			if (row.party_type_fieldname && !fieldnames.includes(row.party_type_fieldname)) {
				frappe.model.set_value(cdt, cdn, "party_type_fieldname", "");
			}
		}
	});
}

function update_party_type_rule_field(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	if (!row || !row.party_type) return;

	// Defensive check: Ensure we are only acting on the correct child table
	if (cdt !== "Party Master Settings Party Type") return;

	frappe.model.with_doctype(row.party_type, () => {
		let meta = frappe.get_meta(row.party_type);
		if (!meta) return;

		let fieldnames = meta.fields
			.filter((d) => !frappe.model.no_value_type.includes(d.fieldtype))
			.map((d) => d.fieldname)
			.sort();

		// Ensure an empty option is available
		if (fieldnames.indexOf("") === -1) {
			fieldnames.unshift("");
		}

		const options_str = fieldnames.join("\n");

		// 1. Official way to set property per row in child table
		frm.set_df_property(
			"party_types",
			"options",
			options_str,
			frm.doc.name,
			"rule_fieldname",
			cdn
		);

		// 2. Direct grid manipulation for immediate visual feedback
		let grid = frm.fields_dict.party_types?.grid;
		if (grid) {
			let grid_row = grid.get_row(cdn);
			if (grid_row) {
				if (grid_row.fields_dict && grid_row.fields_dict["rule_fieldname"]) {
					let field = grid_row.fields_dict["rule_fieldname"];
					if (field && field.df) {
						field.df.options = options_str;
						field.refresh();
					}
				}
				// Force grid row refresh
				grid.refresh_row(cdn);
			}
		}
	});
}
