frappe.provide("frappe.treeview_settings");

frappe.treeview_settings["Party Master"] = {
  breadcrumb: "Party",
  title: __("Chart of Party"),
  get_tree_root: true,
  onload: function (treeview) {
    function expand_node(node, level) {
      if (level > 3) return; // Stop at level 3

      frappe.db
        .get_list("Party Master", {
          filters: { parent_party_master: node.data.value },
          fields: ["name"],
        })
        .then((children) => {
          if (children.length > 0) {
            node.toggle(); // Expand node
            setTimeout(() => {
              node.children.forEach((child) => expand_node(child, level + 1));
            }, 500); // Delay for smooth expansion
          }
        });
    }

    setTimeout(() => {
      treeview.root_node.children.forEach((child) => expand_node(child, 1));
    }, 1000);
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
  
  fields: [
    {
      fieldtype: "Data",
      fieldname: "party_name",
      label: __("Party Name"),
      reqd: 1,
    },

    {
      fieldtype: "Data",
      fieldname: "party_number",
      mandatory_depends_on: "eval:doc.is_group",
      label: __("Party Number"),
      description: __(
        "If not Group Type You can leave it empty" ),
    },
    {
      fieldtype: "Check",
      fieldname: "is_group",
      label: __("Is Group"),
      description: __(
        "Further accounts can be made under Groups, but entries can be made against non-Groups"
      ),
    },
    {
      fieldtype: "Select",
      fieldname: "party_type",
      label: __("Party Type"),
      options: ["Customer", "Supplier", "Employee", "Shareholder"].join("\n"),
    },
    {
      fieldtype: "Link",
      fieldname: "parent_party_master",
      label: __("Parent Party"),
      options: "Party Master",
      filters:{is_group:1},
      
    },
    // Add your custom fields below
  ],
  toolbar: [
		{
			label: __("Add Child"),
			click: function (node,btn) {
        let parent=node.data.value;
        frappe.ui.form.make_quick_entry("Party Master", null, (dialog)=>{
          dialog.set_value("parent_party_master", parent);
          dialog.set_value("is_group", 0);
        }, );
      },
      
			btnClass: "hidden-xs",
		},
		{
			
			label: __("View Ledger"),
			click: function (node, btn) {
				frappe.route_options = {
					from_date: erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[1],
					to_date: erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[2],
		
				};
				frappe.set_route("query-report", "General Ledger");
			},
			btnClass: "hidden-xs",
		},
	],
	extend_toolbar: true,
};
