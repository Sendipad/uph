// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt
frappe.ui.form.on("Auto Text Generator Rule", {
	onload(frm) {
		frm.trigger("setup_field_options");
	},
	refresh(frm) {
		let template_field = frm.get_field("template");
		if (!template_field) return;

		let wrapper = $(template_field.wrapper);

		if (!wrapper.find(".jinja-template-example").length) {
			wrapper.after(`
                <div class="jinja-template-example"
                    style="margin-top: 15px; padding: 15px;
                           background-color: #f8f9fa; border-radius: 3px;
                           border: 1px solid #dfe3e6; font-family: sans-serif;">
                    <h5 style="margin-bottom: 10px; color: #2e3b4a;">
                        ${__("مثال على قالب Jinja لإنشاء ملاحظات الدفع")}
                    </h5>
                    <pre style="white-space: pre-wrap; font-family: monospace; background: #f0f0f0;
                                padding: 12px; border-radius: 4px; overflow-x: auto;">
{%- set remark = "" -%}
{%- if doc.payment_type == "Receive" -%}
  {%- set remark = "استلام مبلغ " ~ doc.received_amount ~ " " ~ doc.paid_to_account_currency ~ " من " ~ doc.party_type ~ " " ~ doc.party -%}
{%- elif doc.payment_type == "Pay" -%}
  {%- set remark = "دفع مبلغ " ~ doc.paid_amount ~ " " ~ doc.paid_from_account_currency ~ " إلى " ~ doc.party_type ~ " " ~ doc.party -%}
{%- elif doc.payment_type == "Internal Transfer" -%}
  {%- set remark = "تحويل داخلي بقيمة " ~ doc.paid_amount ~ " " ~ doc.paid_from_account_currency ~ " من الحساب " ~ doc.paid_from ~ " إلى الحساب " ~ doc.paid_to -%}
{%- endif -%}
{%- if doc.mode_of_payment -%}
  {%- set remark = remark ~ " بواسطة " ~ doc.mode_of_payment -%}
{%- endif -%}
{{ remark.strip() }}
                    </pre>
                </div>
            `);
		}
	},
	setup_field_options(frm) {
		if (frm.doc.document_type) {
			uph.utils.FieldOptionHelper.load({
				documentType: frm.doc.document_type,
				callback(options) {
					uph.utils.FieldOptionHelper.applyAutocomplete(
						frm,
						options,
						["remark_fieldname"], // parent fields
					);
					uph.utils.FieldOptionHelper.applyAutocomplete(
						frm,
						options,
						["fieldname"],
						"conditions", // parent fields
					);
				},
			});
		}
	},

	document_type: function (frm) {
		frm.trigger("setup_field_options");
	},
	get_dependcy_fields(frm) {
		if (!frm.doc.document_type) {
			frappe.msgprint(__("Please select a Document Type first"));
			return;
		}

		uph.utils.FieldOptionHelper.load({
			documentType: frm.doc.document_type,
			callback(options) {
				// Build list of fieldnames to show
				let fieldnames = options.map((opt) => ({
					label: `${opt.label || opt.fieldname} (${opt.fieldtype})`,
					value: opt.value,
				}));

				frappe.prompt(
					[
						{
							fieldname: "selected_fields",
							label: __("Select Dependency Fields"),
							fieldtype: "MultiCheck",
							options: fieldnames.map((f) => ({
								label: `${f.label}`,
								value: f.value,
								checked: frm.doc.dependency_fields?.includes(f.value),
							})),
						},
					],
					(values) => {
						frm.set_value("dependency_fields", values.selected_fields.join(","));
					},
					__("Select Fields"),
				);
			},
		});
	},
});
