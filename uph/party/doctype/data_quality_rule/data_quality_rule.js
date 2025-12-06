// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Data Quality Rule', {
    refresh: function (frm) {
        if (frm.doc.document_type) {
            frm.trigger('load_field_options');
            frm.trigger('set_trigger_options');
        }

        if (!frm.is_new()) {
            frm.add_custom_button(__('Test Rule'), function () {
                frm.trigger('show_test_dialog');
            });
        }
    },

    document_type: function (frm) {
        if (frm.doc.document_type) {
            frm.trigger('load_field_options');
            frm.trigger('set_trigger_options');
        }
    },

    set_trigger_options: function (frm) {
        if (!frm.doc.document_type) return;

        frappe.model.with_doctype(frm.doc.document_type, function () {
            const meta = frappe.get_meta(frm.doc.document_type);
            let options = [];
            if (meta.is_submittable) {
                options = ['On Submit'];
            } else {
                options = ['On Save'];
            }
            set_field_options('trigger', options);

            // Set default if current value is invalid
            if (!options.includes(frm.doc.trigger)) {
                frm.set_value('trigger', options[0]);
            }
        });
    },

    show_test_dialog: function (frm) {
        if (!frm.doc.conditions || frm.doc.conditions.length === 0) {
            frappe.msgprint(__('Please add at least one condition to test the rule.'));
            return;
        }

        // Build dialog fields from rule conditions
        let dialog_fields = [];

        // Add a section for test data
        dialog_fields.push({
            fieldtype: 'Section Break',
            label: __('Test Data')
        });

        // Get unique fields from conditions (avoid duplicates)
        let unique_fields = {};
        frm.doc.conditions.forEach(condition => {
            if (condition.field && !unique_fields[condition.field]) {
                unique_fields[condition.field] = true;

                // Get field metadata from the document type
                frappe.model.with_doctype(frm.doc.document_type, function () {
                    const meta = frappe.get_meta(frm.doc.document_type);
                    let field_meta = null;

                    // Handle dotted paths (child table fields)
                    if (condition.field.includes('.')) {
                        const parts = condition.field.split('.');
                        const child_table_field = parts[0];
                        const child_field = parts[1];

                        // For child tables, we'll use a simple text field
                        dialog_fields.push({
                            label: __(condition.field),
                            fieldname: condition.field.replace('.', '_'),
                            fieldtype: 'Data',
                            description: __('Child table field: {0}', [condition.field])
                        });
                    } else {
                        // Parent field
                        field_meta = meta.fields.find(f => f.fieldname === condition.field);

                        if (field_meta) {
                            dialog_fields.push({
                                label: field_meta.label || __(condition.field),
                                fieldname: condition.field,
                                fieldtype: field_meta.fieldtype || 'Data',
                                options: field_meta.options,
                                description: __('Condition: {0}', [condition.check_type])
                            });
                        } else {
                            // Field not found in meta, use generic Data field
                            dialog_fields.push({
                                label: __(condition.field),
                                fieldname: condition.field,
                                fieldtype: 'Data',
                                description: __('Condition: {0}', [condition.check_type])
                            });
                        }
                    }
                });
            }
        });

        // Add column break for better layout
        if (dialog_fields.length > 3) {
            dialog_fields.splice(Math.ceil(dialog_fields.length / 2), 0, {
                fieldtype: 'Column Break'
            });
        }

        const d = new frappe.ui.Dialog({
            title: __('Test Rule: {0}', [frm.doc.rule_name]),
            fields: dialog_fields,
            size: 'large',
            primary_action_label: __('Find Duplicates'),
            primary_action: function (values) {
                d.hide();

                // Build a test document from the values
                let test_doc = {
                    doctype: frm.doc.document_type
                };

                // Map dialog values to document fields
                Object.keys(values).forEach(key => {
                    // Handle dotted paths (convert back from underscore)
                    let field_name = key;
                    if (!frm.doc.conditions.find(c => c.field === key)) {
                        // This might be a dotted path that was converted
                        field_name = key.replace('_', '.');
                    }
                    test_doc[key] = values[key];
                });

                frappe.call({
                    method: 'uph.controllers.mdm.api.test_rule_with_data',
                    args: {
                        rule_name: frm.doc.name,
                        test_data: test_doc
                    },
                    freeze: true,
                    freeze_message: __('Running Deduplication Check...'),
                    callback: function (r) {
                        if (r.message && r.message.length > 0) {
                            frm.trigger('show_test_results', r.message);
                        } else {
                            frappe.msgprint({
                                title: __('Test Results'),
                                message: __('No duplicates found matching the test data.'),
                                indicator: 'green'
                            });
                        }
                    }
                });
            }
        });

        d.show();
    },

    show_test_results: function (frm, results) {
        if (!results || results.length === 0) {
            frappe.msgprint(__('No duplicates found.'));
            return;
        }

        let html = `
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>${__('Document')}</th>
                        <th>${__('Title')}</th>
                        <th>${__('Score')}</th>
                    </tr>
                </thead>
                <tbody>
        `;

        results.forEach(res => {
            html += `
                <tr>
                    <td><a href="/app/${frappe.router.slug(frm.doc.document_type)}/${res.name}" target="_blank">${res.name}</a></td>
                    <td>${res.title || ''}</td>
                    <td>${parseFloat(res.score).toFixed(2)}</td>
                </tr>
            `;
        });

        html += `</tbody></table>`;

        const d = new frappe.ui.Dialog({
            title: __('Test Results'),
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'results_html',
                    options: html
                }
            ]
        });
        d.show();
    },

    load_field_options: function (frm) {
        uph.utils.FieldOptionHelper.load({
            documentType: frm.doc.document_type,
            callback: (options) => {
                uph.utils.FieldOptionHelper.applyAutocomplete(
                    frm,
                    options,
                    ['field'],
                    'conditions'
                );
            }
        });
    }
});

frappe.ui.form.on('Data Quality Rule Condition', {
    form_render: function (frm, cdt, cdn) {
        if (frm.doc.document_type) {
            uph.utils.FieldOptionHelper.load({
                documentType: frm.doc.document_type,
                callback: (options) => {
                    uph.utils.FieldOptionHelper.applyAutocomplete(
                        frm,
                        options,
                        ['field'],
                        'conditions',
                        cdn
                    );
                }
            });
        }
    },

    field: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.field || !frm.doc.document_type) return;

        const fieldtype = uph.utils.FieldOptionHelper.getFieldType(frm.doc.document_type, row.field);
        let options = ["Exact Match"];

        if (['Date', 'Datetime'].includes(fieldtype)) {
            options.push("Date Range");
        } else if (['Data', 'Text', 'Small Text', 'Long Text', 'Code', 'Text Editor'].includes(fieldtype)) {
            options.push("Fuzzy Match");
        }

        // Use the helper to update options for check_type in the grid
        const check_type_options = options.map(opt => ({ value: opt, label: opt }));
        uph.utils.FieldOptionHelper.applyAutocomplete(
            frm,
            check_type_options,
            ['check_type'],
            'conditions',
            cdn
        );

        // Reset value if invalid
        if (!options.includes(row.check_type)) {
            frappe.model.set_value(cdt, cdn, 'check_type', "Exact Match");
        }
    }
});