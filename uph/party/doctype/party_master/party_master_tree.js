frappe.treeview_settings["Party Master"] = {
	breadcrumb: "Party",
	title: __("Chart of Party"),
	root_label: "Party Master",
	get_tree_nodes: "uph.party.doctype.party_master.party_master.get_children",
	ignore_fields: ["parent_party_master"],

	on_get_node: function (nodes, deep = false) {
		if (frappe.boot.user.can_read.indexOf("GL Entry") == -1) return;

		let party_master = deep
			? nodes.reduce((pm, node) => [...pm, ...node.data], [])
			: nodes.map((node) => node.label);

		frappe.call({
			method: "uph.party.doctype.party_master.party_master.get_party_master_balances",
			args: {
				name: party_master,
				company: cur_tree.args.company,
			},
			callback: function (r) {
				if (!r.message) return;

				r.message.forEach((pm) => {
					const node = cur_tree.nodes[pm.name];
					if (!node || node.is_root) return;

					node.$tree_link.find(".balance-area").remove();

					const balance_text = pm.balances
						.map((balance) => {
							const is_dr = balance.amount >= 0;
							const arrow = is_dr ? "▲" : "▼";
							const color = is_dr ? "red" : "green";
							return `<span style="color:${color}">${arrow} ${format_currency(Math.abs(balance.amount), balance.currency)}</span>`;
						})
						.join(" / ");

					$('<span class="balance-area pull-right">' + balance_text + "</span>").insertAfter(
						node.$tree_link.find("a"),
					);
				});
			},
		});
	},

	filters: [
		{
			fieldname: "company",
			fieldtype: "Select",
			options: erpnext.utils.get_tree_options("company"),
			label: __("Company"),
			default: erpnext.utils.get_tree_default("company"),
		},
		{
			fieldname: "name",
			fieldtype: "Link",
			options: "Party Master",
			label: __("Party Master"),
			onchange: function () {
				const treeview = frappe.views.trees["Party Master"];
				const field = this.df;
				const input = this.$input;
				const party_master = input ? input.get_value() : null;

				if (!party_master) {
					treeview.root_value = null;
					treeview.root_label = treeview.opts.root_label;
					treeview.make_tree();
					return;
				}

				// Check if selected node is a leaf
				frappe.call({
					method: "frappe.client.get_value",
					args: {
						doctype: "Party Master",
						filters: { name: party_master },
						fieldname: ["is_group", "parent_party_master"],
					},
					callback: (r) => {
						if (r.message.is_group) {
							// Handle group node normally
							treeview.root_value = party_master;
							treeview.root_label = party_master;
							treeview.make_tree();
						} else {
							// For leaf node, get its parent and set as root
							const parent = r.message.parent_party_master;

							// Set parent as root
							treeview.root_value = parent;
							treeview.root_label = parent;

							// Make tree with parent as root
							treeview.make_tree();

							// After render, show only the selected leaf under parent
							setTimeout(() => {
								const parent_node = cur_tree.nodes[parent];
								if (parent_node) {
									// Collapse all other children
									//cur_tree.load_children(parent_node, false);

									// Expand only our selected leaf
									const leaf_node = cur_tree.nodes[party_master];
									if (leaf_node) {
										leaf_node.show();
										leaf_node.parent_node.expand();
									}
								}
							}, 500);
						}
					},
				});
			},
		},
	],

	post_render: function (treeview) {
		treeview.page.set_title(__("Chart of Party"));
		treeview.page.set_primary_action(__("New"), function () {
			frappe.ui.form.make_quick_entry("Party Master", null, null);
		});
	},

	toolbar: [
		{
			label: __("Add Child"),
			condition: function (node) {
				return node.expandable;
			},
			click: function (node) {
				frappe.ui.form.make_quick_entry("Party Master", null, null, {
					parent_party_master: node.label,
				});
			},
			btnClass: "hidden-xs",
		},
		{
			label: __("Edit"),
			click: function (node) {
				frappe.set_route("Form", "Party Master", node.label);
			},
			btnClass: "hidden-xs",
		},
		{
			label: __("View Ledger"),
			click: function (node) {
				frappe.route_options = {
					party_master: node.label,
					company: cur_tree.args.company,
				};
				frappe.set_route("query-report", "Party Account Statement");
			},
			btnClass: "hidden-xs",
		},
	],
	extend_toolbar: false,
};
