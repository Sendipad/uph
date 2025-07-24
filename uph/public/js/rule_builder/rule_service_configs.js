// file: apps/uph/uph/public/js/utils/rule_service_config.js

$(document).on("app_ready", function () {
	/**
	 * Register Deduplication UI Config
	 */
	uph.hub.serviceRegistry.register("Deduplication", {
		Rule: {
			defaults: {
				match_threshold: 85,
			},
			fields: [
				{
					fieldname: "match_threshold",
					label: "Match Threshold",
					fieldtype: "Int",
					reqd: 1,
					default: 85,
				},
			],
		},
		"Rule Condition": {
			defaults: {
				left_value_source: "Document Field",
				operator: "==",
				scorer: "JaroWinkler",
			},
			fields_hidden: [
				"left_value_source",
				"right_field_path",
				"right_value_method",
				"right_method_parameters",
			],
			fields: [
				{
					fieldname: "left_value_source",
					default: "Document Field",
					hidden: 1,
				},
				{
					fieldname: "left_field_path",
					label: __("Comparing a"),
				},
				{
					fieldname: "operator",
					label: __("Comparison Operator"),
					options: [
						{ label: __("Fuzzy Match"), value: "fuzzy_match" },
						{ label: __("Exact"), value: "==" },
					],
				},
				{
					fieldname: "scorer",
					fieldtype: "Select",
					options: ["Levenshtein", "JaroWinkler", "Exact"],
					mandatory_depends_on: "eval:doc.operator === 'fuzzy_match'",
				},
			],
			vue: {
				grid: ["left_value_source", "operator", "scorer"],
				layout: "compact",
				depends_on: "eval:doc.is_group==0",
			},
			hooks: {
				validate: (doc) => {
					if (doc.scorer && !doc.left_field_path) {
						throw "Scorer requires a field path";
					}
				},
			},
		},
	});

	/**
	 * Register Normalization UI Config
	 */
	uph.hub.serviceRegistry.register("Normalization Service", {
		"Rule Condition": {
			defaults: {
				left_value_source: "Document Field",
				transformation: "lowercase",
			},
			fields: [
				{
					fieldname: "left_field_path",
					label: __("Field to Normalize"),
					reqd: 1,
				},
				{
					fieldname: "transformation",
					label: __("Transformation Type"),
					fieldtype: "Select",
					options: ["lowercase", "uppercase", "strip_punct", "custom"],
				},
				{
					fieldname: "custom_transformation_method",
					depends_on: "eval:doc.transformation === 'custom'",
				},
			],
			vue: {
				grid: ["left_field_path", "transformation", "custom_transformation_method"],
			},
		},
	});

	/**
	 * Register Integrity Validation UI Config (basic sample)
	 */
	uph.hub.serviceRegistry.register("Integrity Validation", {
		"Rule Condition": {
			defaults: {
				left_value_source: "Document Field",
				operator: "==",
			},
			fields: [
				{
					fieldname: "left_field_path",
					label: __("Left Field"),
					reqd: 1,
				},
				{
					fieldname: "operator",
					label: __("Operator"),
					fieldtype: "Select",
					options: ["==", "!=", "is set", "is not set", "regex_match"],
				},
				{
					fieldname: "right_field_path",
					label: __("Right Field"),
					depends_on: "eval:doc.operator != 'is set' && doc.operator != 'is not set'",
				},
			],
			vue: {
				grid: ["left_field_path", "operator", "right_field_path"],
				layout: "auto",
			},
		},
	});
});

/*
uph.hub.ruleServiceUIConfigs.register("Normalization Service", {
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
	});

	// Integrity Validation Configuration
	uph.hub.ruleServiceUIConfigs.register("Integrity Validation", {
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
	});
registerServiceUIConfig("Deduplication", 
});


{
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
	});*/
