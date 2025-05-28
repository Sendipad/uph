frappe.ui.form.on("Deduplication Job", {
	setup(frm) {
		frm._field_options = {};
	},

	document_type(frm) {
		if (frm.doc.document_type) {
			update_field_options(frm);
		}
	},

	refresh(frm) {
		if (!frm.doc.__islocal) {
			update_field_options(frm);

			frm.add_custom_button(__("Run Now"), () => {
				frappe.call({
					method: "uph.unified_data_tools.run_jobs.enqueue_job",
					args: { job_name: frm.doc.name },
					callback: () => frappe.show_alert(__("Job queued for execution")),
				});
			});

			frm.add_custom_button(__("Clear Cache"), () => {
				frappe.call({
					method: "uph.unified_data_tools.services.cache.RedisCache.clear",
					args: { doctype: frm.doc.document_type },
					callback: () => frappe.show_alert(__("Cache cleared")),
				});
			});
		}
	},
});

frappe.ui.form.on("Deduplication Job Rule", {
	field_path(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.field_path) return;

		const doctype = frm.doc.document_type;
		if (!frm._field_options[doctype]) {
			frappe.show_alert("Field options still loading...");
			return;
		}

		const fieldtype = get_field_type(frm, row.field_path);
		frappe.model.set_value(cdt, cdn, "field_type", fieldtype);

		const is_child = row.field_path.includes(".");
		const strategies = get_strategies_for_type(fieldtype, is_child);

		// ✅ Get grid row to update per-row select field
		const grid = frm.fields_dict.rules.grid;
		const grid_row = grid.get_row(cdn);

		if (grid_row) {
			const operator_field = grid_row.get_field("operator");
			operator_field.df.options = strategies.map((s) => s.label).join("\n");
			operator_field.refresh();
		}

		// Set default value via model
		frappe.model.set_value(cdt, cdn, "operator", strategies[0]?.value || "exact");
		frm.fields_dict.rules.grid.refresh();
	},

	operator(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		const df = frappe.meta.get_docfield(cdt, "tolerance", cdn);
		const show = ["date_range", "percentage", "range"].includes(row.operator);
		df.hidden = !show;

		frm.fields_dict.rules.grid.refresh();
	},
});

// === Helpers ===

function update_field_options(frm) {
	const doctype = frm.doc.document_type;

	if (frm._field_options[doctype]) {
		set_autocomplete_options(frm, frm._field_options[doctype]);
		return;
	}

	frappe.call({
		method: "uph.unified_data_tools.utils.field.get_field_options",
		args: { doctype },
		callback(r) {
			if (r.message) {
				frm._field_options[doctype] = r.message;
				set_autocomplete_options(frm, r.message);
			}
		},
	});
}

function set_autocomplete_options(frm, options) {
	const grid = frm.fields_dict.rules.grid;
	const autocomplete_set = options.map((f) => f.value).join("\n");

	// Update docfield default options
	grid.update_docfield_property("field_path", "options", autocomplete_set);
	frm.fields_dict.on_doc_rules.grid.update_docfield_property(
		"fieldname",
		"options",
		autocomplete_set,
	);
	frm.fields_dict.on_doc_rules.grid.update_docfield_property(
		"with_fieldname",
		"options",
		autocomplete_set,
	);

	// Update open rows
	grid.grid_rows?.forEach((row) => {
		const field = row.grid_form?.fields_dict?.field_path;
		if (field) {
			field.df.options = options.map((f) => f.value);
			field.refresh();
		}
	});

	frm.refresh_field("rules");
	frm.refresh_field("on_doc_rules");
}

function get_field_type(frm, field_path) {
	const doctype = frm.doc.document_type;
	const options = frm._field_options[doctype] || [];
	const match = options.find((f) => f.value === field_path);
	return match?.fieldtype || "Data";
}
function get_strategies_for_type(fieldtype, is_child = false) {
	if (fieldtype === "Table" || is_child) {
		return [
			{ label: "Any Item Exists", value: "any_item" },
			{ label: "All Items Exist", value: "all_items" },
		];
	}

	const strategies = {
		Data: [
			{ label: "Exact Match", value: "exact" },
			{ label: "Contains", value: "contains" },
			{ label: "Starts With", value: "starts_with" },
			{ label: "Fuzzy Match", value: "fuzzy" },
		],
		Date: [
			{ label: "Exact Date", value: "exact_date" },
			{ label: "Within Days", value: "date_range" },
		],
		Datetime: [
			{ label: "Exact Timestamp", value: "exact" },
			{ label: "Within Time Range", value: "date_range" },
		],
		Int: [
			{ label: "Exact Number", value: "exact" },
			{ label: "Within Range", value: "range" },
			{ label: "Percent Difference", value: "percentage" },
		],
		Float: [
			{ label: "Exact Number", value: "exact" },
			{ label: "Within Range", value: "range" },
			{ label: "Percent Difference", value: "percentage" },
		],
		Link: [
			{ label: "Exact Match", value: "exact" },
			{ label: "Fuzzy Match", value: "fuzzy" },
		],
		Select: [{ label: "Exact Match", value: "exact" }],
	};

	return strategies[fieldtype] || [{ label: "Exact Match", value: "exact" }];
}
