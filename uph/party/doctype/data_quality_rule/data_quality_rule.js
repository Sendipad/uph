// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Data Quality Rule', {
    refresh: function(frm) {
        if (frm.doc.document_type) {
            frm.trigger('load_field_options');
        }
    },

    document_type: function(frm) {
        if (frm.doc.document_type) {
            frm.trigger('load_field_options');
        }
    },

    load_field_options: function(frm) {
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
    form_render: function(frm, cdt, cdn) {
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

    field: function(frm, cdt, cdn) {
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