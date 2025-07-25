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

		const updated = store.update_conditions();

		if (typeof updated === "string") {
			frappe.throw(updated); // error message
		}

		if (Array.isArray(updated)) {
			frm.set_value("conditions", updated);
		}
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
		// ✅ If doc name changed (e.g. Ctrl+B → new doc), reset store
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

// Cleanup on form close
frappe.ui.form.on("Rule", "before_unload", function (frm) {
	if (frm.rule_builder) {
		frm.rule_builder.$rule_builder.$destroy();
		frm.rule_builder.isMounted = false;
		delete frm.rule_builder;
	}
});
