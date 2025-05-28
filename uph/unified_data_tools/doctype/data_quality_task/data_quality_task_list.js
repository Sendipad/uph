frappe.listview_settings["Data Quality Task"] = {
	hide_name_column: true,
	title_field: "note",

	add_fields: [
		"reference_type",
		"reference_name",
		"priority",
		"document_type",
		"docname_a",
		"note", // ✅ Added
	],
	formatters: {
		note(value) {
			// Convert HTML string to plain text
			return $("<div>").html(value).text();
		},
	},

	onload(listview) {
		listview.page.set_title(__("To Resolve Documents"));
		listview.page.add_inner_button("Open Both Records", () => {
			const selected = listview.get_checked_items();
			if (selected.length) {
				selected.forEach((item) => {
					frappe.set_route("Form", item.document_type, item.docname_a);
					frappe.set_route("Form", item.document_type, item.docname_b);
				});
			} else {
				frappe.msgprint("Select at least one result.");
			}
		});

		listview.page.add_menu_item(__("Clear Logs"), function () {
			frappe.call({
				method:
					"uph.unified_data_tools.doctype.data_quality_task.data_quality_task.clear_deduplication_job_results",
				callback: function () {
					listview.refresh();
				},
			});
		});

		frappe.require("logtypes.bundle.js", () => {
			frappe.utils.logtypes.show_log_retention_message(cur_list.doctype);
		});
	},

	button: {
		show: function (doc) {
			return doc.docname_a;
		},
		get_label: function () {
			return __("Open", null, "Access");
		},
		get_description: function (doc) {
			return __("Open {0}", [`${__(doc.reference_type)}: ${doc.reference_name}`]);
		},
		action: function (doc) {
			frappe.set_route("Form", doc.doctype, doc.name);
		},
	},
};
