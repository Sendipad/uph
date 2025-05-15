app_name = "uph"
app_title = "Unified Party Hub"
app_publisher = "Abdo Mohammed Ruzaqi"
app_description = "Unified Party Hub (UPH) is a Frappe-based extension for ERPNext designed to centralize and organize all party-related entities in a structured hierarchy. It introduces the Party Master, a tree-based Doctype that serves as a single source of truth for managing different party types (Customers, Suppliers, Employees, Shareholders, etc.), allowing businesses to efficiently support multi-currencies business transacition classify and track relationships."
app_email = "ruzaqi@gmail.com"
app_license = "gpl-3.0"

# Apps
# ------------------

required_apps = ["erpnext"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "uph",
# 		"logo": "/assets/uph/logo.png",
# 		"title": "Unified Party Hub",
# 		"route": "/uph",
# 		"has_permission": "uph.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/uph/css/uph.css"
# app_include_js = "/assets/uph/js/uph.js"

# include js, css files in header of web template
# web_include_css = "/assets/uph/css/uph.css"
# web_include_js = "/assets/uph/js/uph.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "uph/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}
app_include_js = [
    "uph.bundle.js",
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
# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "uph.utils.jinja_methods",
# 	"filters": "uph.utils.jinja_filters"
# }

# Installation
# ------------

after_install = "uph.setup.install.setup"
# after_install = "uph.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "uph.uninstall.before_uninstall"
# after_uninstall = "uph.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "uph.utils.before_app_install"
# after_app_install = "uph.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "uph.utils.before_app_uninstall"
# after_app_uninstall = "uph.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "uph.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways
after_migrate = ["uph.setup.install.on_migrate"]

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }
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
        "before_validate": "uph.party.controllers.party.validate_party_master_on_document_types",
        "validate": "uph.party.controllers.party.validate_party_master_on_target_party_type",
        "on_update": [
            "uph.party.controllers.party.validate_party_master_on_target_party_type"
        ],
        "on_change": [
            "uph.party.controllers.party.validate_party_master_on_document_types"
        ],
        "on_trash": "uph.party.controllers.party.validate_party_master_on_target_party_type",
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
export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
