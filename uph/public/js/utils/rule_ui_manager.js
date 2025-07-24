frappe.provide("uph.hub");

// Rule Controller Class
uph.hub.RuleController = class {
	constructor(frm) {
		this.frm = frm;
		this.setup();
	}

	setup() {
		this.setup_queries();
		this.setup_ui_configurations();
		this.bind_condition_row_form();
		this.apply_ui_customizations();
	}

	setup_queries() {
		this.frm.set_query("document_type", () => {
			return {
				filters: {
					is_submittable: 0,
					istable: 0,
				},
			};
		});
	}

	setup_ui_configurations() {
		this.rule_service_configs = {
			Deduplication: this.get_deduplication_config(),
			"Normalization Service": this.get_normalization_config(),
			"Integrity Validation": this.get_validation_config(),
		};
	}

	apply_ui_customizations() {
		if (!this.frm.doc.rule_service_type) return;

		const config = this.rule_service_configs[this.frm.doc.rule_service_type] || {};
		this.customize_grid("conditions", config.condition_config);
		this.customize_grid("actions", config.action_config);
		this.customize_parent_form(config.parent_form_config);
	}

	customize_grid(fieldname, config = {}) {
		try {
			const grid = this.frm.fields_dict[fieldname]?.grid;
			if (!grid) return;

			// Store config for row form access
			grid._rule_config = config;

			const all_fields = (grid.docfields || []).map((df) => df.fieldname);
			const visible_fields = config.visible_fields || [];

			// Update field properties
			all_fields.forEach((field) => {
				const should_show = visible_fields.includes(field);
				grid.update_docfield_property(field, "hidden", !should_show);

				// Set field options if configured
				if (config.field_options?.[field]) {
					grid.update_docfield_property(field, "options", config.field_options[field]);
				}

				// Set field defaults if configured
				if (config.field_defaults?.[field]) {
					grid.update_docfield_property(field, "default", config.field_defaults[field]);
				}
			});

			// Apply column configuration
			if (config.column_config && grid.grid_columns) {
				grid.grid_columns.forEach((col) => {
					if (config.column_config.show) {
						col.hidden = !config.column_config.show.includes(col.fieldname);
					}
					if (config.column_config.labels?.[col.fieldname]) {
						col.label = config.column_config.labels[col.fieldname];
					}
				});

				// Refresh headers using Frappe's API
				if (grid.refresh_headers && typeof grid.refresh_headers === "function") {
					grid.refresh_headers();
				}
			}

			// Refresh grid field
			this.frm.refresh_field(fieldname);
		} catch (e) {
			console.error(`Error customizing ${fieldname} grid:`, e);
		}
	}

	customize_parent_form(config = {}) {
		const fields = [
			"document_type",
			"apply_scopes",
			"conditions",
			"actions",
			"debug_mode",
			"priority",
			"default_alert_message",
			"match_threshold",
		];

		// Set visibility
		fields.forEach((field) => {
			const hidden = (config.hidden_fields || []).includes(field);
			this.frm.set_df_property(field, "hidden", hidden);
		});

		// Set defaults
		Object.entries(config.field_defaults || {}).forEach(([field, val]) => {
			if (this.frm.fields_dict[field]) {
				this.frm.set_value(field, val);
			}
		});

		this.frm.refresh_fields();
	}

	bind_condition_row_form() {
		// Handler for condition rows
		frappe.ui.form.on("Rule Condition", {
			form_render: (frm, cdt, cdn) => {
				this.handle_row_form_render("conditions", cdt, cdn);
			},
		});

		// Handler for action rows
		frappe.ui.form.on("Rule Action", {
			form_render: (frm, cdt, cdn) => {
				this.handle_row_form_render("actions", cdt, cdn);
			},
		});
	}

	handle_row_form_render(fieldname, cdt, cdn) {
		try {
			const row = locals[cdt][cdn];
			const grid = this.frm.fields_dict[fieldname]?.grid;
			if (!grid) return;

			// Use Frappe's get_row() method instead of grid_rows_by_docname
			const grid_row = grid.get_row(cdn);
			if (!grid_row) return;

			const form = grid_row.form;
			if (!form || !form.fields_dict) return;

			// Apply field visibility
			const config = grid._rule_config || {};
			const visible_fields = config.visible_fields || [];

			Object.keys(form.fields_dict).forEach((field) => {
				const hidden = !visible_fields.includes(field);
				form.set_df_property(field, "hidden", hidden);
			});

			// Special handling for operator label in conditions
			if (fieldname === "conditions" && form.fields_dict.operator) {
				form.fields_dict.operator.df.label = `Operator (${row.left_field_path || "?"})`;
				form.fields_dict.operator.refresh();
			}
		} catch (e) {
			console.error(`Error handling ${fieldname} row form:`, e);
		}
	}

	// CORRECTED METHOD NAMES:
	get_deduplication_config() {
		return {
			condition_config: {
				visible_fields: [
					"left_value_source",
					"left_field_path",
					"operator",
					"scorer",
					"weight",
					"comparison_strategy",
				],
				field_options: {
					operator: ["fuzzy_match", "==", "is set", "is not set"],
					scorer: ["Fuzz Ratio", "Fuzz Partial Ratio", "Token Sort Ratio", "Token Set Ratio"],
				},
				field_defaults: {
					operator: "fuzzy_match",
					scorer: "Fuzz Ratio",
					weight: 1.0,
				},
				column_config: {
					show: ["left_field_path", "operator", "scorer", "weight"],
					labels: {
						left_field_path: "Compare Field",
						scorer: "Match Scorer",
						weight: "Score Weight",
					},
				},
			},
			action_config: {
				visible_fields: ["action_type", "alert_message", "notification_recipients"],
				field_options: {
					action_type: ["Link Duplicate Records", "Notify Users", "Create Data Quality Log Entry"],
				},
				column_config: {
					show: ["action_type", "alert_message"],
					labels: {
						action_type: "Action",
						alert_message: "Message Text",
					},
				},
			},
			parent_form_config: {
				hidden_fields: [],
				field_defaults: { match_threshold: 80 },
			},
		};
	}

	// FIXED METHOD NAME: get_normalization_config (was get_normalization_config)
	get_normalization_config() {
		return {
			condition_config: {
				visible_fields: [
					"left_value_source",
					"left_field_path",
					"operator",
					"right_value_literal",
					"regex_pattern",
					"negate_condition",
				],
				field_options: {
					operator: ["==", "!=", "is set", "is not set", "regex_match", "normalize_field"],
				},
				field_defaults: { operator: "normalized_field" },
				column_config: {
					show: ["left_field_path", "normalization_profile"],
					labels: { left_field_path: "Normalized Field" },
				},
			},
			action_config: {
				visible_fields: [
					"action_type",
					"target_field",
					"action_value_data",
					"notification_recipients",
					"notification_template",
				],
				field_options: {
					action_type: [
						"Set Field Value",
						"Create Normalization Record",
						"Notify Users",
						"Create Data Quality Log Entry",
					],
				},
			},
			parent_form_config: {
				hidden_fields: ["match_threshold"],
			},
		};
	}

	get_validation_config() {
		return {
			condition_config: {
				visible_fields: [
					"left_value_source",
					"left_field_path",
					"operator",
					"right_value_source",
					"right_value_literal",
					"expression_value",
					"comparison_strategy",
					"negate_condition",
					"left_specific_doctype",
					"right_specific_doctype",
				],
				field_options: {
					operator: [
						"==",
						"!=",
						">",
						"<",
						">=",
						"<=",
						"contains",
						"not contains",
						"in",
						"not in",
						"is set",
						"is not set",
						"value_changed",
					],
				},
				column_config: {
					show: ["left_field_path", "operator"],
					labels: { left_field_path: "Validation Field" },
				},
			},
			action_config: {
				visible_fields: [
					"action_type",
					"alert_message",
					"notification_recipients",
					"notification_template",
					"target_field",
					"source_variable",
					"method_name",
					"parameters",
					"result_variable",
				],
				field_options: {
					action_type: [
						"Raise Alert (Error)",
						"Raise Alert (Warning)",
						"Raise Alert (Info)",
						"Notify Users",
						"Set Field Value",
						"Call Registered Method",
						"Create Data Quality Log Entry",
						"Flag Record for Review",
					],
				},
			},
			parent_form_config: {
				hidden_fields: ["match_threshold"],
			},
		};
	}
};
/* The code snippet you provided is setting up form event handlers for the "Rule" doctype in Frappe
framework. */
