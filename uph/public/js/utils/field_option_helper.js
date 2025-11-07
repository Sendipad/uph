//file uph/public/js/utils/field_option_helper.js

frappe.provide("uph.utils");
frappe.provide("uph.hub");

uph.hub.docfields = {
	cache: {},

	get_docfields(document_type, basefieldname = null, callback) {
		let key = Array.isArray(document_type) ? document_type.slice().sort().join(",") : document_type;

		let cached = this.cache[key];

		if (cached && basefieldname) {
			const child = cached.child_tables?.[basefieldname];
			if (child) {
				callback?.(child);
				return;
			}
		}

		if (cached && !basefieldname) {
			callback?.(cached);
			return;
		}

		frappe.call({
			method: "uph.hub.utils.field.get_field_path",
			args: { doctype: document_type, basefieldname: basefieldname },
			callback: (r) => {
				if (r.message?.fields) {
					r.message.fields.forEach((field) => {
						if (field.label) {
							field.label = __(field.label);
						}
					});
				}
				callback(r.message);
			},
		});
	},
};

uph.utils.FieldOptionHelper = {
	cache: {},
	load({ documentType, callback }) {
		if (Array.isArray(documentType)) {
			// استخدم الكاش للمصفوفة المفتاحية
			const key = documentType.join(",");
			if (this.cache[key]) {
				callback?.(this.cache[key]);
				return;
			}

			// استدعاء API جلب الحقول المشتركة للمجموعة دفعة واحدة
			frappe.call({
				method: "uph.hub.utils.field.get_common_fields_in_doctypes",
				args: { doctypes: JSON.stringify(documentType) },
				callback: (r) => {
					if (Array.isArray(r.message)) {
						this.cache[key] = r.message;
						callback?.(r.message);
					} else {
						callback?.([]);
					}
				},
			});
			return;
		}

		// حالة مستند واحد فقط
		if (this.cache[documentType]) {
			callback?.(this.cache[documentType]);
			return;
		}

		frappe.call({
			method: "uph.hub.utils.field.get_field_options",
			args: { doctype: documentType },
			callback: (r) => {
				if (Array.isArray(r.message)) {
					this.cache[documentType] = r.message;
					callback?.(r.message);
				} else {
					callback?.([]);
				}
			},
		});
	},

	load_field_options_for_conditions(frm) {
		const rule_doc_types = (frm.doc.apply_scopes || [])
			.map((entry) => entry.document_type)
			.filter(Boolean);

		const unique_doc_types = [...new Set(rule_doc_types)];
		if (!unique_doc_types.length) return;

		this.load({
			documentType: unique_doc_types,
			callback: (commonFields) => {
				frm.field_option_cache = commonFields;

				// تحديث قيم الحقول لكل صفوف الشروط (مثلاً تهيئة الحقول)
				(frm.doc.conditions || []).forEach((d) => {
					frappe.model.set_value(d.doctype, d.name, "left_field_path", "");
				});
			},
		});
	},

	getFieldType(documentType, fieldPath) {
		const field = this.cache[documentType]?.find((f) => f.value === fieldPath);
		return field?.fieldtype || "Data";
	},

	getField(documentType, fieldPath) {
		return this.cache[documentType]?.find((f) => f.value === fieldPath) || null;
	},

	hasFieldOption(documentType, fieldPath) {
		return !!this.cache[documentType]?.some((f) => f.value === fieldPath);
	},

	applyAutocomplete(frm, options, fieldnames = [], tableField = null, row_name = null) {
		const values = options.map((f) => f.value);
		if (tableField) {
			const grid = frm.fields_dict[tableField]?.grid;
			if (!grid) return;

			fieldnames.forEach((fieldname) => {
				grid.update_docfield_property(fieldname, "options", values);

				const rows = row_name ? [grid.grid_rows_by_docname?.[row_name]] : grid.grid_rows || [];

				rows.forEach((row) => {
					const field = row?.grid_form?.fields_dict?.[fieldname];
					if (field) {
						field.df.options = values;
						field.make_input();
					}
				});
			});

			frm.refresh_field(tableField);
		} else {
			fieldnames.forEach((fieldname) => {
				frm.set_df_property(fieldname, "options", values);
				frm.fields_dict[fieldname].make_input();
				frm.refresh_field(fieldname);
			});
		}
	},
};

/*frappe.provide("uph.utils");
uph.utils.FieldOptionHelper = {
  cache: {},

  load({ documentType, callback }) {
    if (this.cache[documentType]) {
      callback?.(this.cache[documentType]);
      return;
    }

    frappe.call({
      method: "brh.unified_data_tools.utils.field.get_field_options",
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


  applyAutocomplete(frm, options, fieldnames = [], tableField = null) {
    const values = options.map((f) => f.value);
    if (tableField) {
      // Child table fields
      const grid = frm.fields_dict[tableField]?.grid;
      if (!grid) return;

      fieldnames.forEach((fieldname) => {
        grid.update_docfield_property(fieldname, "options", values);
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


  getFieldType(documentType, fieldPath) {
    const field = this.cache[documentType]?.find((f) => f.value === fieldPath);
    return field?.fieldtype || "Data";
  },


  getField(documentType, fieldPath) {
    return this.cache[documentType]?.find((f) => f.value === fieldPath) || null;
  },


  hasFieldOption(documentType, fieldPath) {
    return !!this.cache[documentType]?.some((f) => f.value === fieldPath);
  },
};
*/

//file uph/public/js/utils/field_option_helper.js
/** 
frappe.provide("uph.utils");

uph.utils.FieldOptionHelper = {
	cache: {},

	
	load({ documentType, callback }) {
		if (Array.isArray(documentType)) {
			// Multiple doctypes → get intersection
			this.loadCommonFields({ documentTypes: documentType, callback });
			return;
		}

		if (this.cache[documentType]) {
			callback?.(this.cache[documentType]);
			return;
		}

		frappe.call({
			method: "uph.hub.utils.field.get_field_options",
			args: { doctype: documentType },
			callback: (r) => {
				if (Array.isArray(r.message)) {
					this.cache[documentType] = r.message;
					callback?.(r.message);
				} else {
					callback?.([]);
				}
			},
		});
	},

	load_field_options_for_conditions(frm) {
		const rule_doc_types = (frm.doc.apply_scopes || [])
			.map((entry) => entry.document_type)
			.filter(Boolean);

		const unique_doc_types = [...new Set(rule_doc_types)];
		if (!unique_doc_types.length) return;

		uph.utils.FieldOptionHelper.load({
			documentType: unique_doc_types,
			callback: (commonFields) => {
				frm.field_option_cache = commonFields;

				// Update each row (after they're actually loaded)
				(frm.doc.conditions || []).forEach((d, i) => {
					frappe.model.set_value(d.doctype, d.name, "left_field_path", ""); // or keep existing
				});
			},
		});
	},

	loadCommonFields({ documentTypes, callback }) {
		let loaded = 0;
		const results = {};
		const total = documentTypes.length;

		const tryFinish = () => {
			if (loaded < total) return;

			// Now calculate intersection
			const allFields = documentTypes.map((dt) => results[dt].map((f) => f.value));
			const commonFieldnames = allFields.reduce((a, b) => a.filter((v) => b.includes(v)));

			const fieldDefs = results[documentTypes[0]].filter((f) => commonFieldnames.includes(f.value));

			callback?.(fieldDefs);
		};

		documentTypes.forEach((doctype) => {
			if (this.cache[doctype]) {
				results[doctype] = this.cache[doctype];
				loaded++;
				tryFinish();
			} else {
				frappe.call({
					method: "uph.hub.utils.field.get_field_options",
					args: { doctype },
					callback: (r) => {
						if (Array.isArray(r.message)) {
							this.cache[doctype] = r.message;
							results[doctype] = r.message;
						} else {
							results[doctype] = [];
						}
						loaded++;
						tryFinish();
					},
				});
			}
		});
	},
 
frappe.provide("uph.utils");

uph.utils.FieldOptionHelper = {
	cache: {},

	load({ documentType, callback }) {
		if (Array.isArray(documentType)) {
			// **استخدم API واحدة على السيرفر للحصول على الحقول المشتركة**
			if (this.cache[documentType.join(",")]) {
				callback?.(this.cache[documentType.join(",")]);
				return;
			}

			frappe.call({
				method: "uph.hub.utils.field.get_common_fields_in_doctypes",
				args: { doctypes: JSON.stringify(documentType) },
				callback: (r) => {
					if (Array.isArray(r.message)) {
						this.cache[documentType.join(",")] = r.message;
						callback?.(r.message);
					} else {
						callback?.([]);
					}
				},
			});
			return;
		}

		// حالة doctype واحد: استدعاء API التي تعيد كل الحقول
		if (this.cache[documentType]) {
			callback?.(this.cache[documentType]);
			return;
		}

		frappe.call({
			method: "uph.hub.utils.field.get_field_options",
			args: { doctype: documentType },
			callback: (r) => {
				if (Array.isArray(r.message)) {
					this.cache[documentType] = r.message;
					callback?.(r.message);
				} else {
					callback?.([]);
				}
			},
		});
	},

	// يمكن حذف loadCommonFields لأنها لم تعد ضرورية
	loadCommonFields({ documentTypes, callback }) {
		// فقط لاستدعاء load مع المصفوفة
		this.load({ documentType: documentTypes, callback });
	},

	applyAutocomplete(frm, options, fieldnames = [], tableField = null, row_name = null) {
		const values = options.map((f) => f.value);
		if (tableField) {
			const grid = frm.fields_dict[tableField]?.grid;
			if (!grid) return;

			fieldnames.forEach((fieldname) => {
				grid.update_docfield_property(fieldname, "options", values);

				// Only update specific row if row_name provided
				const rows = row_name ? [grid.grid_rows_by_docname?.[row_name]] : grid.grid_rows || [];

				rows.forEach((row) => {
					const field = row?.grid_form?.fields_dict?.[fieldname];
					if (field) {
						field.df.options = values;
						field.make_input(); // critical to update input
					}
				});
			});

			frm.refresh_field(tableField);
		} else {
			fieldnames.forEach((fieldname) => {
				frm.set_df_property(fieldname, "options", values);
				frm.fields_dict[fieldname].make_input();
				frm.refresh_field(fieldname);
			});
		}
	},

	getFieldType(documentType, fieldPath) {
		const field = this.cache[documentType]?.find((f) => f.value === fieldPath);
		return field?.fieldtype || "Data";
	},

	getField(documentType, fieldPath) {
		return this.cache[documentType]?.find((f) => f.value === fieldPath) || null;
	},

	hasFieldOption(documentType, fieldPath) {
		return !!this.cache[documentType]?.some((f) => f.value === fieldPath);
	},
};
**/
