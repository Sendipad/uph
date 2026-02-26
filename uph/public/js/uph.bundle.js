//file:apps/uph/uph/public/js/uph.bundle.js
if (typeof frappe !== 'undefined') {
    frappe.provide("uph");
}

import "./utils/party.js";
import "./utils/party_master_manager.js";
import "./utils/utils.js";
import "./utils/field_option_helper.js";
//import "./rule_builder/rule_service_configs.js";
//import "./utils/rule_ui_config_registry";
//import "./rule_builder/rule_builder.js"; // contains RuleBuilder class
//import "./rule_builder/rule_builder_mount.js"; // mounts RuleBuilder using class

//mport "./components/RuleBuilder.vue";
//import "./utils/rule_service_configs";
//import "./utils/rule_ui_manager";
//import "./utils/rule__js";
//import "./rule_form";

$(document).on('app_ready', function () {
    if (!frappe.session || !frappe.boot) return;
    const isAdmin = frappe.session.user === 'Administrator' || (frappe.user_roles || []).includes('System Manager');
    if (isAdmin && frappe.boot.uph_setup_needed) {
        const route = frappe.get_route();
        if (!route) return;

        // Target UPH Form and Tree views for enforcement
        const isFormView = route[0] === 'Form' && ['Party Master', 'Party Issue', 'Party Master Settings'].includes(route[1]);
        const isTreeView = route[0] === 'Tree' && route[1] === 'Party Master';

        if ((isFormView || isTreeView) && route[0] !== 'uph-setup-wizard') {
            frappe.show_alert({
                message: __('UPH Setup is required. Redirecting to Setup Wizard...'),
                indicator: 'orange'
            });
            setTimeout(() => {
                frappe.set_route('uph-setup-wizard');
            }, 1000);
        }
    }
});
