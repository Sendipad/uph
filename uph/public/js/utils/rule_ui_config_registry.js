// 🧠 مخزن التكوينات حسب نوع خدمة القاعدة
frappe.provide("uph.rule");

const configs = {};

// ✅ دالة التسجيل - يستخدمها المطورون لإضافة إعدادات لكل خدمة
function registerServiceUIConfig(serviceType, config) {
	configs[serviceType] = config;
}

// ✅ دالة الاسترجاع - تُستخدم داخل RuleBuilder.vue لقراءة التكوين
function getServiceUIConfig(serviceType) {
	return configs[serviceType] || { fields: [] };
}

// ✅ تسجيل في مساحة Frappe المنظمة

uph.rule.registerServiceUIConfig = registerServiceUIConfig;
uph.rule.getServiceUIConfig = getServiceUIConfig;
/*
// Configuration registration
$(document).on("app_ready", function () {
	const cfg = uph.rule.ruleServiceUIConfigs;

	cfg.register("Deduplication", {
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
	});

	cfg.register("Normalization Service", {
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

	cfg.register("Integrity Validation", {
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
});
*/
