// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt
frappe.ui.form.on("Normalization Profile", {
	validate_pipeline_and_parameters_changed(frm, confirm = false) {
		if (!frm.is_new()) return false;
		if (
			frm.doc.pipeline !== frm._original_pipeline ||
			frm.doc.parameters !== frm._original_parameters
		) {
			if (confirm) {
				frappe.confirm(
					__(
						"Pipeline or Parameters have changed. This will affect Normalized Record. Do you want to save?",
					),
					() => {
						frm.save();
					},
					() => {
						frm.reload_doc();
					},
				);
			} else {
				return true;
			}
		}
	},
	refresh(frm) {
		if (!frm.is_new()) {
			frm._original_pipeline = frm.doc.pipeline;
			frm._original_parameters = frm.doc.parameters;
		}

		frm.add_custom_button("🔍 Preview Normalization", () => {
			frappe.prompt(
				{
					label: "Sample Input",
					fieldname: "sample_text",
					fieldtype: "Data",
					reqd: 1,
				},
				(values) => {
					let args = { value: values.sample_text };
					if (frm.is_new() || frm.events.validate_pipeline_and_parameters_changed(frm)) {
						args.profile = frm.doc.pipeline;
						args.parameters = frm.doc.parameters;
					} else {
						args.profile = frm.doc.name;
					}
					frappe.call({
						method: "uph.hub.utils.normalizer.normalizer",
						args: args,
						callback(r) {
							if (!r.exc) {
								frappe.msgprint({
									title: __("Normalized Output"),
									message: r.message,
									indicator: "blue",
								});
							}
						},
					});
				},
				__("Preview Normalization"),
				__("Normalize"),
			);
		});
	},
	pipeline(frm) {
		if (frm.doc.pipeline) {
			const unique = [...new Set(frm.doc.pipeline.split(",").map((m) => m.trim()))];
			frm.set_value("pipeline", unique.join(","));
		}
	},
	get_pipeline_template(frm) {
		const templates = {
			default:
				"trim_whitespace,unicode_normalize,remove_diacritics,casefold,character_translation,normalize_whitespace",
			strict_arabic:
				"trim_whitespace,unicode_normalize,remove_diacritics,casefold,character_translation,normalize_whitespace",
			clean_text:
				"trim_whitespace,unicode_normalize,remove_diacritics,casefold,character_translation,remove_punctuation,normalize_whitespace",
			light: "trim_whitespace,casefold",
			email: "trim_whitespace,email_normalize",
			phone: "trim_whitespace,phone_format",
			numeric: "trim_whitespace,numeric_only",
			alphanumeric: "trim_whitespace,alphanumeric_only",
		};

		frappe.prompt(
			{
				label: "Select Template",
				fieldname: "template",
				fieldtype: "Select",
				options: Object.keys(templates),
				reqd: 1,
			},
			(values) => {
				frm.set_value("pipeline", templates[values.template]);
			},
			__("Insert from Template"),
			__("Set"),
		);
	},
});
