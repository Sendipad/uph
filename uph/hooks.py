app_name = "uph"
app_title = "Unified Party Hub"
app_publisher = "Abdo Mohammed Ruzaqi"
app_description = "Unified Party Hub (UPH) is a Frappe-based extension for ERPNext designed to centralize and organize all party-related entities in a structured hierarchy. It introduces the Party Master, a tree-based Doctype that serves as a single source of truth for managing different party types (Customers, Suppliers, Employees, Shareholders, etc.), allowing businesses to efficiently support multi-currencies business transacition classify and track relationships."
app_email = "ruzaqi@gmail.com"
app_license = "gpl-3.0"

# Apps
# ------------------

required_apps = ["erpnext"]

app_include_js = [
    "uph.bundle.js",
    "public/js/rule_builder/rule_builder.js",  # NOT rule_builder_app.js
]
# include js in page
# page_js = {"page" : "public/js/file.js"}
treeviews = ["Party Master"]

docment_type_with_custom_js = ["Sales Invoice", "Payment Entry", "Journal Entry"]
# include js in doctype views
doctype_js = {
    "Sales Invoice": "public/js/erpnext/sales_invoice.js",
    "Payment Entry": "public/js/erpnext/payment_entry.js",
    "Journal Entry": "puplic/js/erpnext/journal_entry.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "uph/public/icons.svg"
boot_session = "uph.party.boot.add_pm_doctypes"


after_install = "uph.setup.install.setup"

# after_migrate = [
#    "uph.hub.services.registry.sync_rule_service_types",
#    "uph.setup.install.on_migrate",
# ]

tx_doctype_with_party_master = [
    "Sales Invoice",
    "Purchase Invoice",
    "Journal Entry Account",
    "Payment Entry",
    "Sales Order",
    "Purchase Order",
    "Delivery Note",
    "Purchase Receipt",
    "Expense Claim",
]
# Document Events
# ---------------
# Hook on document methods and events
parties_type = ["Customer", "Supplier", "Employee"]
doc_events = {
    "*": {
        "before_insert": [
            "uph.unified_data_tools.doc_hooks.run_deduplication_job_on_doc",
            "uph.unified_data_tools.doc_hooks.run_record_integrity_rule_on_doc",
            "uph.unified_data_tools.doc_hooks.generate_custom_remarks_on_doc",
        ],
        "before_save": [
            "uph.unified_data_tools.doc_hooks.run_deduplication_job_on_doc",
            "uph.unified_data_tools.doc_hooks.run_record_integrity_rule_on_doc",
            "uph.unified_data_tools.doc_hooks.generate_custom_remarks_on_doc",
        ],
        "validate": [
            "uph.party.controllers.party.validate_party_master_on_target_party_type",
            "uph.unified_data_tools.doc_hooks.run_deduplication_job_on_doc",
            "uph.unified_data_tools.doc_hooks.run_record_integrity_rule_on_doc",
            "uph.unified_data_tools.doc_hooks.generate_custom_remarks_on_doc",
        ],
        "on_submit": [
            "uph.unified_data_tools.doc_hooks.run_deduplication_job_on_doc",
            "uph.unified_data_tools.doc_hooks.run_record_integrity_rule_on_doc",
            "uph.unified_data_tools.doc_hooks.generate_custom_remarks_on_doc",
        ],
        "on_cancel": [
            "uph.unified_data_tools.doc_hooks.run_deduplication_job_on_doc",
            "uph.unified_data_tools.doc_hooks.run_record_integrity_rule_on_doc",
            "uph.unified_data_tools.doc_hooks.generate_custom_remarks_on_doc",
        ],
        "on_update_after_submit": [
            "uph.unified_data_tools.doc_hooks.run_deduplication_job_on_doc",
            "uph.unified_data_tools.doc_hooks.run_record_integrity_rule_on_doc",
            "uph.unified_data_tools.doc_hooks.generate_custom_remarks_on_doc",
        ],
        "on_update": [
            "uph.party.controllers.party.validate_party_master_on_target_party_type"
        ],
        "on_change": [
            "uph.party.controllers.party.validate_party_master_on_document_types"
        ],
        "on_trash": [
            "uph.party.controllers.party.validate_party_master_on_target_party_type"
        ],
        "before_validate": [
            "uph.party.controllers.party.validate_party_master_on_document_types"
        ],
    }
}

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }
global_search_doctypes = {
    "Default": [
        {"doctype": "Party Master", "index": 0},
    ]
}
export_python_type_annotations = True

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"uph.tasks.all"
# 	],
# 	"daily": [
# 		"uph.tasks.daily"
# 	],
# 	"hourly": [
# 		"uph.tasks.hourly"
# 	],
# 	"weekly": [
# 		"uph.tasks.weekly"
# 	],
# 	"monthly": [
# 		"uph.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "uph.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "uph.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "uph.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["uph.utils.before_request"]
# after_request = ["uph.utils.after_request"]

# Job Events
# ----------
# before_job = ["uph.utils.before_job"]
# after_job = ["uph.utils.after_job"]

# User Data Protection
# --------------------
# extend_bootinfo=[
# 	"uph.party.doctype.party_master_settings.party_master_settings.add_pm_doctypes"
# ]
# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"uph.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
