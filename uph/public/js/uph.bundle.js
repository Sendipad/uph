//file:apps/uph/uph/public/js/uph.bundle.js
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
    if (frappe.boot.uph_setup_needed) {
        if (frappe.get_route()[0] !== 'setup-wizard') {
            frappe.set_route('setup-wizard');
        }
    }
});
