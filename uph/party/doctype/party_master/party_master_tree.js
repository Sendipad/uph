frappe.provide("frappe.treeview_settings");

frappe.treeview_settings["Party Master"] = {
  breadcrumb: "Party",
  title: __("Chart of Party"),
  root_label: "Party Master",
  get_tree_nodes: "uph.party.doctype.party_master.party_master.get_children",
  ignore_fields: ["parent_party_master"],
  on_get_node: function (nodes, deep = false) {
    if (frappe.boot.user.can_read.indexOf("GL Entry") == -1) return;

    let party_master = [];
    if (deep) {
      // in case of `get_all_nodes`
      party_master = nodes.reduce((pm, node) => [...pm, ...node.data], []);
    } else {
      accounts = nodes;
    }

    const get_balances = frappe.call({
      method: "uph.party.doctype.party_master.party_master.get_party_master_balances",
      args: {
        name: party_master,
        company: cur_tree.args.company,
      },
    });

    get_balances.then((r) => {
      console.log("new", r);
      if (!r.message || r.message.length == 0) return;

      for (let pm of r.message) {
        const node = cur_tree.nodes && cur_tree.nodes[pm.name];
        if (!node || node.is_root) continue;

        // show Dr if positive since balance is calculated as debit - credit else show Cr
        node.parent && node.parent.find(".balance-area").remove();

        // Iterate over the balances for each party master
        const balance_text = pm.balances
          .map((balance) => {
            const dr_or_cr = balance.amount >= 0 ? "Dr" : "Cr";
            return `${format_currency(Math.abs(balance.amount), balance.currency)} ${__(dr_or_cr)}`;
          })
          .join(" / ");

        // Insert the balance information before the node's list
        $(
          `<span class="balance-area pull-right">${balance_text}</span>`
        ).insertBefore(node.$ul);
      }
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
  ],

  // Customizing the toolbar to remove 'Delete' and 'Rename' actions
  toolbar: [
    {
      label: __("Add Child"),
      click: function (node) {
        frappe.ui.form.make_quick_entry("Party Master", null, (doc) => {
          doc.set_value("parent_party_master", node.data.value);
        });
      },
      btnClass: "hidden-xs",
    },
    {
      label: __("View Ledger"),
      click: function (node) {
        frappe.route_options = {
          from_date: erpnext.utils.get_fiscal_year(
            frappe.datetime.get_today(),
            true
          )[1],
          to_date: erpnext.utils.get_fiscal_year(
            frappe.datetime.get_today(),
            true
          )[2],
        };
        frappe.set_route("query-report", "Party Account Statement");
      },
      btnClass: "hidden-xs",
    },
  ],


  extend_toolbar: true,
};
