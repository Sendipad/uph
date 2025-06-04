// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Field Comparison Rule", {
	onload(frm) {
		if (frm.doc.document_type) {
			frm.trigger("set_document_type_auto_complete");
			frm.trigger("set_with_doctype_autocomplete");
		}
	},
	document_type(frm) {
		if (!frm.doc.document_type) return;
		frm.trigger("set_document_type_auto_complete");
	},
	with_doctype(frm) {
		if (frm.doc.type === "Cross-DocType Comparison" && frm.doc.with_doctype) {
			frm.trigger("set_with_doctype_autocomplete");
		}
	},
	set_document_type_auto_complete(frm) {
		if (!frm.doc.document_type && !frm.doc.with_doctype) return;
		let document_type_fields = ["fieldname"];
		if (!frm.doc.with_doctype && frm.doc.type !== "Cross-DocType Comparison") {
			document_type_fields.push("with_field");
		}
		uph.utils.FieldOptionHelper.load({
			documentType: frm.doc.document_type,
			callback(options) {
				uph.utils.FieldOptionHelper.applyAutocomplete(
					frm,
					options,
					document_type_fields, // parent fields
				);
			},
		});
	},
	set_with_doctype_autocomplete(frm) {
		if (frm.doc.type === "Cross-DocType Comparison" && frm.doc.with_doctype) {
			uph.utils.FieldOptionHelper.load({
				documentType: frm.doc.with_doctype,
				callback(options) {
					uph.utils.FieldOptionHelper.applyAutocomplete(
						frm,
						options,
						["with_field"], // parent fields
					);
				},
			});
		}
	},
	fetch_values_for_first_field(frm) {
		handleFieldValueSelection({
			frm,
			doctypeField: "document_type",
			fieldnameField: "fieldname",
			targetField: "field_allowed_values",
		});
	},

	fetch_values_for_second_field(frm) {
		handleFieldValueSelection({
			frm,
			doctypeField: frm.doc.type === "Cross-DocType Comparison" ? "with_doctype" : "document_type",
			fieldnameField: "with_field",
			targetField: "with_field_allowed_values",
		});
	},
	fieldname(frm) {
		if (!frm.doc.document_type || !frm.doc.fieldname) return;

		const fieldtype = uph.utils.FieldOptionHelper.getFieldType(
			frm.doc.document_type,
			frm.doc.fieldname,
		);
		frm.set_value("fieldname_type", fieldtype);
		frm.refresh_field("fieldname_type");
	},

	with_field(frm) {
		const doctype =
			frm.doc.type === "Cross-DocType Comparison" ? frm.doc.with_doctype : frm.doc.document_type;

		if (!doctype || !frm.doc.with_field) return;

		const fieldtype = uph.utils.FieldOptionHelper.getFieldType(doctype, frm.doc.with_field);
		frm.set_value("with_field_type", fieldtype);
		frm.refresh_field("with_field_type");
	},
});

function handleFieldValueSelection({ frm, doctypeField, fieldnameField, targetField }) {
	const doctype = frm.doc[doctypeField];
	const fieldname = frm.doc[fieldnameField];

	if (!doctype || !fieldname) {
		frappe.msgprint("Please ensure both the DocType and Field are selected.");
		return;
	}

	const fieldMeta = uph.utils.FieldOptionHelper.getField(doctype, fieldname);

	if (!fieldMeta || fieldMeta.fieldtype !== "Link") {
		frappe.msgprint(`Field "${fieldname}" is not a Link field.`);
		return;
	}

	if (!fieldMeta.options) {
		frappe.msgprint(`Linked DocType is not set for field "${fieldname}".`);
		return;
	}

	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: fieldMeta.options,
			limit_page_length: 100,
			fields: ["name"],
		},
		callback(r) {
			if (!r.message?.length) {
				frappe.msgprint(`No records found in linked DocType "${fieldMeta.options}".`);
				return;
			}

			const dialog = new frappe.ui.Dialog({
				title: `Select Values for ${fieldname}`,
				size: "extra-large",
				fields: [
					{
						fieldtype: "Table",
						fieldname: "values_table",
						label: "Select Values",
						cannot_add_rows: true,
						data: r.message.map((d) => ({ value: d.name })),
						fields: [
							{
								fieldtype: "Data",
								fieldname: "value",
								in_list_view: 1,
								read_only: 1,
								label: "Value",
							},
						],
					},
				],
				primary_action_label: "Set",
				primary_action() {
					// Get selected rows via grid API
					const table = dialog.fields_dict.values_table.grid;
					const selected = table.get_selected_children().map((row) => row.value);

					if (selected.length) {
						frm.set_value(targetField, selected.join("\n"));
					} else {
						frappe.msgprint("No values selected.");
					}
					dialog.hide();
				},
			});

			dialog.show();
		},
	});
}
