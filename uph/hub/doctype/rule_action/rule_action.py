# Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class RuleAction(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		action_method: DF.Link | None
		action_target_scope: DF.Literal["Current Document", "Related Document", "System", "User Context"]
		action_type: DF.Literal["Set Field Value", "Apply Template To Field", "Call Registered Method", "Raise Alert (Error)", "Raise Alert (Warning)", "Raise Alert (Info)", "Notify Users", "Set Context Variable", "Create Normalization Record", "Create Data Monitoring"]
		action_value_data: DF.Data | None
		action_value_template: DF.Link | None
		alert_message: DF.SmallText | None
		execution_mode: DF.Literal["Immediate (Synchronous)", "Background (Asynchronous)"]
		method_parameters: DF.Code | None
		notification_recipients: DF.SmallText | None
		notification_template: DF.Link | None
		notification_via: DF.Literal["Email", "SMS", "System Notification", "Webhook"]
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		target_field: DF.Autocomplete | None
		target_specifier: DF.Data | None
		template_to_apply: DF.Link | None
		value_source_type: DF.Literal["Literal Value", "Doc Field", "Registered Method Result", "Dynamic Template", "Context Variable"]
	# end: auto-generated types
	pass
