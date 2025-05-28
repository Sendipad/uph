frappe.provide("uph.utils");

uph.utils.FieldOptionHelper = {
	cache: {},

	/**
	 * Load and cache field options for a doctype
	 */
	load({ documentType, callback }) {
		if (this.cache[documentType]) {
			callback?.(this.cache[documentType]);
			return;
		}

		frappe.call({
			method: "uph.unified_data_tools.utils.field.get_field_options",
			args: { doctype: documentType },
			callback: (r) => {
				if (Array.isArray(r.message)) {
					this.cache[documentType] = r.message;
					callback?.(r.message);
				} else {
					callback?.([]); // fallback
				}
			},
		});
	},

	/**
	 * Apply autocomplete options to fields in parent or child table
	 */
	applyAutocomplete(frm, options, fieldnames = [], tableField = null) {
		const values = options.map((f) => f.value);
		if (tableField) {
			// Child table fields
			const grid = frm.fields_dict[tableField]?.grid;
			if (!grid) return;

			fieldnames.forEach((fieldname) => {
				grid.update_docfield_property(fieldname, "options", joined);
				grid.grid_rows?.forEach((row) => {
					const field = row.grid_form?.fields_dict?.[fieldname];
					if (field) {
						field.df.options = values;
						field.refesh();
					}
				});
			});

			frm.refresh_field(tableField);
		} else {
			// Parent fields: needs force input rebuild
			fieldnames.forEach((fieldname) => {
				frm.set_df_property(fieldname, "options", values);
				frm.fields_dict[fieldname].make_input();
				frm.refresh_field(fieldname);
			});
		}
	},

	/**
	 * Get field type from cached options
	 */
	getFieldType(documentType, fieldPath) {
		const field = this.cache[documentType]?.find((f) => f.value === fieldPath);
		return field?.fieldtype || "Data";
	},

	/**
	 * Get raw field definition
	 */
	getField(documentType, fieldPath) {
		return this.cache[documentType]?.find((f) => f.value === fieldPath) || null;
	},

	/**
	 * Check if a given fieldPath exists
	 */
	hasFieldOption(documentType, fieldPath) {
		return !!this.cache[documentType]?.some((f) => f.value === fieldPath);
	},
};
