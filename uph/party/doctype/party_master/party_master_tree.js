frappe.treeview_settings["Party Master"] = {
	breadcrumb: "Party",
	title: __("Chart of Party"),
	root_label: "Party Master",
	get_tree_nodes: "uph.party.doctype.party_master.party_master.get_children",
	ignore_fields: ["parent_party_master"],

	onload: function (treeview) {
		frappe.treeview_settings["Party Master"].treeview = treeview;

		treeview.load_settings = function () {
			return Promise.all([
				frappe.db.get_single_value("Party Master Settings", "auto_expand_levels"),
				frappe.db.get_single_value("Party Master Settings", "hide_balance")
			]).then(([levels, hide_balance]) => {
				treeview.settings = {
					expand_levels: levels || 3,
					hide_balance: hide_balance || 0
				};
				return treeview.settings;
			}).catch(err => {
				// Default if settings not found
				treeview.settings = {
					expand_levels: 3,
					hide_balance: 0
				};
				return treeview.settings;
			});
		};

		// Load settings immediately
		treeview.load_settings();

		treeview.get_company = function () {
			return cur_tree?.args?.company || frappe.defaults.get_user_default("Company");
		};

		treeview.custom_make_new_node = function (parent_node) {
			if (!parent_node || !parent_node.expandable) {
				frappe.msgprint(__("Select a group node first."));
				return;
			}

			frappe.ui.form.make_quick_entry(
				"Party Master",
				function (doc) {
					try {
						if (doc?.name) {
							frappe.show_alert({
								message: __("Created new Party Master {0}", [doc.party_name || doc.name]),
								indicator: "green",
							});
							if (cur_tree && parent_node) {
								parent_node.loaded = false;
								parent_node.expanded = false;
								cur_tree.load_children(parent_node);
							}
						}
					} catch (e) {
						console.error("Error in Party Master creation callback:", e);
					}
				},
				null,
				{
					doctype: "Party Master",
					parent_party_master: parent_node.data?.value || null,
				},
				null,
				frappe.ui.form.PartyMasterQuickEntryForm
			);
		};

		// ✅ Expand to configured levels
		treeview.expand_configured_levels = function () {
			if (!cur_tree?.root_node || !treeview.settings) {
				console.warn("Tree not ready for expansion");
				return;
			}

			const max_levels = treeview.settings.expand_levels;
			if (max_levels <= 0) return; // Don't expand if set to 0

			const expand_recursive = (node, current_level) => {
				if (current_level >= max_levels || !node.expandable) return;

				cur_tree.load_children(node).then(() => {
					setTimeout(() => {
						Object.values(cur_tree.nodes).forEach(child => {
							if (child.parent_node === node) {
								expand_recursive(child, current_level + 1);
							}
						});
					}, 100);
				});
			};

			expand_recursive(cur_tree.root_node, 0);
		};

		// ✅ Add Financial Statement buttons
		for (let report of [
			"Party Account Statement",
			"Party Account Balances",
			"Chronological Party Ledger"
		]) {
			treeview.page.add_inner_button(
				__(report),
				function () {
					const company = treeview.get_company();
					if (!company) {
						frappe.msgprint(__("Please select a Company first"));
						return;
					}
					frappe.set_route("query-report", report, { company: company });
				},
				__("Financial Statements")
			);
		}
	},

	on_get_node: function (nodes, deep = false) {
		const tree = this;
		const settings = frappe.treeview_settings["Party Master"];
		const treeview = settings.treeview;

		if (!tree || !tree.nodes) {
			console.warn("UPH: tree instance not found in on_get_node");
			return;
		}

		if (treeview.settings?.hide_balance) return;
		if (!frappe.boot.user.can_read.includes("GL Entry")) return;

		let party_masters = [];
		if (deep) {
			// Deep load (e.g. initial root load or mass expansion)
			party_masters = nodes.flatMap(n => {
				const data = n.data || n;
				if (Array.isArray(data)) {
					return data.map(item => item?.value);
				}
				return data?.value ? [data.value] : [];
			}).filter(Boolean);
		} else {
			// Normal expansion: nodes are Node objects
			party_masters = nodes.map(n => n?.value || n.data?.value).filter(Boolean);

			// Refresh parent nodes' aggregate balances
			nodes.forEach(n => {
				if (n.parent_node && (n.parent_node.value || n.parent_node.data?.value)) {
					party_masters.push(n.parent_node.value || n.parent_node.data.value);
				}
			});
		}

		if (!party_masters.length) return;

		tree.pending_balance_nodes = tree.pending_balance_nodes || [];
		tree.pending_balance_nodes.push(...party_masters);

		if (tree.balance_debounce_timeout) {
			clearTimeout(tree.balance_debounce_timeout);
		}

		if (tree.pending_balance_nodes.length > 100) {
			settings.flush_balance_requests(tree);
		} else {
			tree.balance_debounce_timeout = setTimeout(() => {
				settings.flush_balance_requests(tree);
			}, 150);
		}
	},

	flush_balance_requests: function (tree) {
		const settings = frappe.treeview_settings["Party Master"];
		const treeview = settings.treeview;

		if (!tree.pending_balance_nodes || !tree.pending_balance_nodes.length) return;

		const batched_names = [...new Set(tree.pending_balance_nodes)];
		tree.pending_balance_nodes = [];


		frappe.call({
			method: "uph.party.doctype.party_master.party_master.get_party_master_balances",
			args: {
				name: batched_names,
				company: treeview.get_company()
			},
			callback: (r) => {
				if (!r.message) return;


				r.message.forEach(pm => {
					const node = tree.nodes[pm.name];
					if (!node || node.is_root) return;

					const balance_html = pm.balances
						.map(balance => {
							const is_dr = balance.amount >= 0;
							const arrow = is_dr ? "▲" : "▼";
							const color = is_dr ? "red" : "green";
							return `<span style="color:${color}; margin-left:10px; font-weight:bold;">${arrow} ${format_currency(
								Math.abs(balance.amount),
								balance.currency
							)}</span>`;
						})
						.join(" / ");

					// Legacy/Fallback for link update
					const $link = node.$tree_link || $(`[data-node-id="${pm.name}"]`);

					// Align with Account Tree Style
					if (node.$ul) {
						// Clean previous
						node.parent && node.parent.find(".balance-area").remove();

						// Insert before Children UL (floats right)
						$(`<span class="balance-area pull-right">${balance_html}</span>`)
							.insertBefore(node.$ul);
					} else if ($link.length) {
						// Fallback for nodes without $ul (e.g. maybe leaves if tree struct differs?)
						// But usually leaves have empty $ul or we can insert after link
						$link.find(".balance-area").remove();
						$(`<span class="balance-area pull-right">${balance_html}</span>`)
							.appendTo($link);
					}
				});
			}
		});
	},

	menu_items: [
		{
			label: __("View List"),
			action: function () {
				frappe.set_route("List", "Party Master");
			},
		},
		{
			label: __("Print"),
			action: function () {
				this.print_tree();
			},
		},
		{
			label: __("Refresh"),
			action: function () {
				this.make_tree();
			},
		}
	],

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
			disable_onchange: true,
			onchange: function () {
				const party_master = this.get_value();
				const treeview = frappe.views.trees["Party Master"];

				if (!party_master) {
					cur_tree.root_value = null;
					cur_tree.root_label = cur_tree.opts.root_label;
					delete cur_tree.args.name;
					treeview.set_title();
					cur_tree.make_tree();
					return;
				}

				frappe.call({
					method: "frappe.client.get_value",
					args: {
						doctype: "Party Master",
						filters: { name: party_master },
						fieldname: ["is_group", "parent_party_master"],
					},
					callback: (r) => {
						if (!r.message) return;

						const { is_group, parent_party_master } = r.message;
						const new_root = is_group ? party_master : (parent_party_master || cur_tree.opts.root_label);

						cur_tree.root_value = new_root;
						cur_tree.root_label = new_root;
						cur_tree.args.name = party_master;
						treeview.set_title();

						cur_tree.make_tree();

						setTimeout(() => {
							treeview.expand_configured_levels();
						}, 500);

						if (!is_group && party_master) {
							setTimeout(() => {
								const leaf_node = cur_tree.nodes[party_master];
								if (leaf_node) {
									cur_tree.on_node_click(leaf_node);
								}
							}, 2000);
						}
					},
				});
			},
		},
	],

	post_render: function (treeview) {
		treeview.page.set_title(__("Chart of Party"));

		// Wait for settings to load before expanding
		setTimeout(() => {
			treeview.expand_configured_levels();
		}, 500);

		treeview.page.set_primary_action(__("New"), function () {
			frappe.ui.form.make_quick_entry(
				"Party Master",
				(doc) => {
					if (doc?.name) {
						frappe.show_alert({
							message: __("Created new Party Master {0}", [doc.party_name || doc.name]),
							indicator: "green",
						});
						treeview.make_tree();
					}
				},
				null,
				{ doctype: "Party Master" },
				null,
				frappe.ui.form.PartyMasterQuickEntryForm
			);
		});
	},

	toolbar: [
		{
			label: __("Add Child"),
			condition: (node) => node.expandable,
			click: function (node) {
				frappe.views.trees["Party Master"].custom_make_new_node(node);
			},
			btnClass: "hidden-xs",
		},
		{
			label: __("Edit"),
			condition: (node) => !node.is_root,
			click: (node) => frappe.set_route("Form", "Party Master", node.label),
			btnClass: "hidden-xs",
		},
		{
			label: __("Create Party"),
			condition: (node) => !node.is_root && !node.expandable,
			click: function (node) {
				uph.party.create_party_for_party_master_from_node(node.label);
			},
			btnClass: "hidden-xs",
		},
		{
			label: __("View Ledger"),
			click: function (node) {
				frappe.route_options = {
					party_master: node.label,
					company: frappe.views.trees["Party Master"].get_company()
				};
				frappe.set_route("query-report", "Party Account Statement");
			},
			btnClass: "hidden-xs",
		},
	],
};