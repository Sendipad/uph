frappe.ui.form.on("Rule", {
	setup(frm) {
		frm.doctypes = [];
	},
	onload(frm) {
		if (frm.is_new() && !frm.doc?.conditions) {
			frappe.listview_settings["Rule"].new_doctype_dialog();
		}
	},
	rule_service_type(frm) {},
	async document_type(frm) {
		if (!frm.doc.document_type) return;

		// Enforce only 1 document_type across apply_scopes
		const conflict = (frm.doc.apply_scopes || []).some(
			(row) => row.document_type && row.document_type !== frm.doc.document_type,
		);

		if (conflict) {
			frappe.msgprint(__("Clearing Apply Scopes to match selected Document Type."));
			frm.clear_table("apply_scopes");
			frm.refresh_field("apply_scopes");
		}

		// Update all existing rows to match new document_type
		(frm.doc.apply_scopes || []).forEach((row) => {
			row.document_type = frm.doc.document_type;
		});
		frm.refresh_field("apply_scopes");

		// Update doctypes for downstream logic
		frm.doctypes = getDocumentTypes(frm);
		await set_field_options(frm);
	},
	async apply_scopes_add(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		const doc_type = frm.doc.document_type;

		if (doc_type) {
			row.document_type = doc_type;
			frm.refresh_field("apply_scopes");
		}

		frm.doctypes = getDocumentTypes(frm);
		await set_field_options(frm);
	},
	refresh(frm) {
		if (frm.doc.apply_scopes && frm.doc.apply_scopes.length) {
			frm.doctypes = getDocumentTypes(frm);
		}
		frm.fields_dict.conditions.grid.wrapper.find(".grid-row-check").hide(); // optional UI tweak
	},
});

frappe.ui.form.on("Rule Condition", {
	form_render: async function (frm, cdt, cdn) {
		const row = frappe.get_doc(cdt, cdn);
		const form = frm.fields_dict.conditions.grid.grid_rows_by_docname?.[row.name]?.form;

		if (!form) return;

		if (!row.is_group) {
			update_conditions_form(frm, row);
		}

		const show = frm.doc.rule_service_type === "Deduplication";
		form.toggle_display("weight", show);

		// ✅ LEFT FIELD OPTIONS (Specific DocType Field)
		if (
			row.left_value_source === "Specific DocType Field" &&
			row.left_specific_doctype &&
			form.fields_dict.left_field_path
		) {
			const leftOpts = await uph.hub.field_options.loadFieldOptions(row.left_specific_doctype);
			if (Array.isArray(leftOpts)) {
				form.fields_dict.left_field_path.df.options = leftOpts;
				form.fields_dict.left_field_path.refresh();
			}
		}
	},
	left_specific_doctype(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.left_value_source === "Specific DocType Field" && row.left_specific_doctype) {
			// Load field options for the specific doctype
			uph.hub.field_options.loadFieldOptions(row.left_specific_doctype).then((options) => {
				if (Array.isArray(options)) {
					row.left_field_path = "";
					frm.refresh_field("conditions");
					set_field_options(frm, "left_field_path", row, options);
				}
			});
		}
	},
});
async function set_field_options(frm, fieldname = null, row = null, options = null) {
	const grid = frm.fields_dict["conditions"].grid;

	// 1. Per-row assignment
	if (fieldname && row && options) {
		const grid_row = grid.grid_rows_by_docname?.[row.name];

		if (!grid_row) return; // row not mounted yet

		const form = grid_row.form;
		if (form?.fields_dict?.[fieldname]) {
			form.fields_dict[fieldname].df.options = options;
			form.fields_dict[fieldname].refresh();
		} else {
			// row is collapsed or not rendered yet — update schema fallback
			grid.update_docfield_property(fieldname, "options", options);
		}
		return;
	}

	// 2. Global fallback update for all doc types
	const doctypes = getDocumentTypes(frm);
	if (!doctypes.length) return;

	const defaultFieldOptions = await uph.hub.field_options.loadFieldOptions(doctypes);

	grid.update_docfield_property("left_field_path", "options", defaultFieldOptions);
	grid.update_docfield_property("right_field_path", "options", defaultFieldOptions);

	// 3. Row-specific override for Specific DocType Fields
	for (const grid_row of grid.grid_rows) {
		const doc = grid_row.doc;

		if (doc.left_value_source === "Specific DocType Field" && doc.left_specific_doctype) {
			const options = await uph.hub.field_options.loadFieldOptions(doc.left_specific_doctype);
			await set_field_options(frm, "left_field_path", doc, options);
		}

		if (doc.right_value_source === "Specific DocType Field" && doc.right_specific_doctype) {
			const options = await uph.hub.field_options.loadFieldOptions(doc.right_specific_doctype);
			await set_field_options(frm, "right_field_path", doc, options);
		}
	}
}

function getDocumentTypes(frm) {
	const types = (frm.doc.apply_scopes || [])
		.map((row) => row.document_type)
		.filter(Boolean)
		.filter((value, index, self) => self.indexOf(value) === index);

	if (!types.length && frm.doc.document_type) {
		types.push(frm.doc.document_type);
	}
	return types.sort();
}
function updateGridField(frm, table, fieldname, prop, value) {
	const grid = frm.fields_dict[table].grid;
	grid.update_docfield_property(fieldname, prop, value);
	grid.debounced_refresh();
}

function updateChildRowField(frm, table, rowname, fieldname, prop, value) {
	const grid = frm.fields_dict[table].grid;
	const row = grid.get_row(rowname);
	const df = row.docfields.find((f) => f.fieldname === fieldname);
	if (df) {
		df[prop] = value;
		row.refresh_field(fieldname);
	}
}

function set_column_disp(frm) {
	let rule_service_type = frm.doc.rule_service_type;
	if (!rule_service_type) return;
	let config = uph.rule.getServiceUIConfig(rule_service_type);
	if (!config) return;
	let fields = config.column_config?.show || [];
	let labels = config.column_config?.labels || {};
	let grid = frm.fields_dict.conditions.grid;
	if (!grid) return;
	// Update grid columns
	grid.grid_columns.forEach((col) => {
		if (fields.includes(col.fieldname)) {
			col.hidden = false;
			if (labels[col.fieldname]) {
				col.label = labels[col.fieldname];
			}
		} else {
			col.hidden = true;
		}
	});
	// Refresh grid headers
	if (grid.refresh_header && typeof grid.refresh_header === "function") {
		grid.refresh_headers();
	}
}
function update_conditions_form(frm, row) {
	var rule;
	const grid = frm.fields_dict.conditions.grid;
	if (!grid) return;

	// Get the form for the current row
	const form = grid.grid_rows_by_docname[row.name]?.form;
	if (!form || !form.fields_dict) return;

	// Update field visibility based on service type
	const servicetype = frm.doc.rule_service_type;
	const showWeight = servicetype === "Deduplication";

	form.toggle_display("weight", showWeight);
}
