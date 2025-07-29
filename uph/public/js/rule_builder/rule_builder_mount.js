//file: apps/uph/uph/public/js/rule_builder/rule_builder_mount.js

frappe.ui.form.on("Rule", {
	onload(frm) {
		frm.page.sidebar.hide();
		initRuleBuilder(frm);
	},

	refresh(frm) {
		initRuleBuilder(frm);
	},

	apply_scopes_add(frm, cdt, cdn) {
		frm.events.updateDocumentTypesWithDebounce(frm);
	},

	apply_scopes_remove(frm, cdt, cdn) {
		frm.events.updateDocumentTypesWithDebounce(frm);
	},

	apply_scopes_update(frm, cdt, cdn) {
		frm.events.updateDocumentTypesWithDebounce(frm);
	},

	// CORRECTED DEBOUNCE FUNCTION
	updateDocumentTypesWithDebounce: frappe.utils.debounce(function (frm) {
		const documentTypes = this.getUniqueDocumentTypes(frm);
		if (frm.rule_builder) {
			frm.rule_builder.updateDocumentTypes(documentTypes);
		}
	}, 300),

	getUniqueDocumentTypes(frm) {
		const types = (frm.doc.apply_scopes || [])
			.map((row) => row.document_type)
			.filter(Boolean)
			.filter((value, index, self) => self.indexOf(value) === index);

		if (!types.length && frm.doc.document_type) {
			types.push(frm.doc.document_type);
		}
		return types.sort();
	},
	before_save(frm) {
		const store = frm.rule_builder?.store;
		if (!store) return;

		const updates = store.update_conditions(); // rows from Vue with `.name`
		if (typeof updates === "string") {
			frappe.throw(updates); // validation error
		}

		const meta = frappe.get_meta("Rule Condition");
		const allowed_fields = meta.fields.map((df) => df.fieldname);
		const table = frm.doc.conditions;

		const updateNames = new Set(updates.map((row) => row.name));
		const grid = frm.fields_dict["conditions"].grid;

		// STEP 1: Remove rows not in updates
		for (let i = table.length - 1; i >= 0; i--) {
			const row = table[i];
			if (!updateNames.has(row.name)) {
				table.splice(i, 1); // Remove from doc
				grid.grid_rows_by_docname[row.name]?.remove(); // Clean UI
				frm.dirty();
			}
		}

		// STEP 2: Add new or update existing
		for (let row of updates) {
			let existing = table.find((d) => d.name === row.name);
			if (existing) {
				for (const key of allowed_fields) {
					if (row.hasOwnProperty(key)) {
						existing[key] = row[key];
					}
				}
			} else {
				const newRow = frm.add_child("conditions");
				for (const key of allowed_fields) {
					if (row.hasOwnProperty(key)) {
						newRow[key] = row[key];
					}
				}
			}
		}
		frm.dirty();

		frm.refresh_field("conditions");

		console.table(
			frm.doc.conditions.map((row) => ({
				name: row.name,
				idx: row.idx,
				condition_id: row.condition_id,
				__islocal: row.__islocal,
			})),
		);
	},
	on_tab_change(frm) {
		const currentTab = frm.get_active_tab()?.label;

		if (currentTab === "Rule Builder") {
			frm.footer.wrapper.hide();
			frm.form_wrapper.find(".form-message").hide();
			frm.form_wrapper.addClass("mb-1");
			initRuleBuilder(frm);
		} else {
			frm.footer.wrapper.show();
			frm.form_wrapper.find(".form-message").show();
			frm.form_wrapper.removeClass("mb-1");
		}
	},
});

function initRuleBuilder(frm) {
	const documentTypes = getDocumentTypes(frm);
	const wrapper = frm.get_field("rule_builder_html")?.$wrapper?.get(0);

	if (!wrapper) return;

	const currentDocName = frm.doc?.name;

	if (!frm.rule_builder) {
		frm.rule_builder = new uph.ui.RuleBuilder({
			wrapper,
			frm,
			serviceType: frm.doc.rule_service_type,
			documentTypes,
		});
	} else {
		if (frm.rule_builder.store?.doc?.name !== currentDocName) {
			frm.rule_builder.store.init(frm, frm.doc.rule_service_type, documentTypes);
		} else {
			frm.rule_builder.updateDocumentTypes(documentTypes);
		}
	}
}

function getDocumentTypes(frm) {
	const types = (frm.doc.apply_scopes || [])
		.map((row) => row.document_type)
		.filter(Boolean)
		.filter((value, index, self) => self.indexOf(value) === index);

	if (!types.length && frm.doc.document_type) {
		types.push(frm.doc.document_type);
	}
	return types.sort();
}

frappe.ui.form.on("Rule", "before_unload", function (frm) {
	if (frm.rule_builder) {
		frm.rule_builder.$rule_builder.$destroy();
		frm.rule_builder.isMounted = false;
		delete frm.rule_builder;
	}
});
