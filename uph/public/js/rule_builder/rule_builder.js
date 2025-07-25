//file: apps/uph/uph/public/js/rule_builder/rule_builder.js
import { createApp, watchEffect } from "vue";
import { createPinia } from "pinia";
import { useRuleBuilderStore } from "./store.js";
import RuleBuilderComponent from "./RuleBuilder.vue";

class RuleBuilder {
	constructor({ wrapper, frm, serviceType, documentTypes }) {
		this.$wrapper = $(wrapper);
		this.frm = frm;
		this.page = frm.page;
		this.serviceType = serviceType;
		this.documentTypes = documentTypes;
		this.read_only = frm.is_read_only;
		this.isMounted = false; // Track mount status

		this.init();
	}

	init() {
		this.setup_page_actions();
		this.setup_app();
		this.watch_changes();
		this.isMounted = true; // Mark as mounted
	}

	setup_page_actions() {
		this.test_btn?.remove();
		this.undo_btn?.remove();
		this.redo_btn?.remove();
		this.add_group_btn?.remove();

		if (!this.read_only) {
			this.test_btn = this.page.add_button(__("Test Rule"), () => {
				this.store.testRule();
			});

			this.undo_btn = this.page
				.add_button(__("Undo"), () => {
					this.store.undo();
				})
				.addClass("btn-default");

			this.redo_btn = this.page
				.add_button(__("Redo"), () => {
					this.store.redo();
				})
				.addClass("btn-default");

			this.add_group_btn = this.page
				.add_button(__("Add Group"), () => {
					this.store.addConditionGroup();
				})
				.addClass("btn-default");
		}
	}

	setup_app() {
		const pinia = createPinia();
		const app = createApp(RuleBuilderComponent);

		app.config.globalProperties.__ = window.__ || ((s) => s);
		app.config.errorHandler = (err) => {
			frappe.msgprint({
				title: __("Application Error"),
				message: err.message,
				indicator: "red",
			});
		};

		app.use(pinia);
		this.store = useRuleBuilderStore();
		this.store.init(this.frm, this.serviceType, this.documentTypes);
		app.provide("ruleBuilderStore", this.store);

		this.$rule_builder = app.mount(this.$wrapper.get(0));
	}
	updateDocumentTypes(newDocumentTypes) {
		// Normalize to sorted unique array
		const normalizedTypes = [...new Set(newDocumentTypes)].sort();

		if (this.store) {
			// Only update if types actually changed
			const currentTypes = [...new Set(this.store.documentTypes)].sort();
			const sameTypes =
				currentTypes.length === normalizedTypes.length &&
				currentTypes.every((val, idx) => val === normalizedTypes[idx]);

			if (!sameTypes) {
				this.store.documentTypes = normalizedTypes;
				this.store.markDirty();
			}
		}
	}
	watch_changes() {
		watchEffect(() => {
			if (this.store.dirty) {
				this.page.set_indicator(__("Unsaved"), "orange");
			} else {
				this.page.clear_indicator();
			}
		});
	}
}

frappe.provide("uph.ui");
uph.ui.RuleBuilder = RuleBuilder;

// Cleanup on form close
frappe.ui.form.on("Rule", "before_unload", function (frm) {
	if (frm.rule_builder) {
		frm.rule_builder.$rule_builder.$destroy();
		frm.rule_builder.isMounted = false;
		delete frm.rule_builder;
	}
});

export default RuleBuilder;
