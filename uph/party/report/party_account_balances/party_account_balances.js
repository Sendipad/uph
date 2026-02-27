// Copyright (c) 2025, Abdo Mohammed Ruzaqi and contributors
// For license information, please see license.txt

frappe.query_reports["Party Account Balances"] = {
  filters: [
    {
      fieldname: "company",
      label: __("Company"),
      fieldtype: "Link",
      options: "Company",
      default: frappe.defaults.get_user_default("Company"),
      reqd: 1,
    },
    {
      fieldname: "party_master",
      label: __("Party"),
      fieldtype: "MultiSelectList",
      options: "Party Master",
      get_data: (txt) => {
        const is_group = frappe.query_report.get_filter_value("is_group");
        const filters = {};
        if (is_group !== undefined && is_group !== null) {
          filters.is_group = is_group ? 1 : 0;
        }
        return frappe.db.get_link_options("Party Master", txt, filters);
      },
    },

    {
      fieldname: "to_date",
      label: __("End Date"),
      fieldtype: "Date",
      default: frappe.datetime.get_today(),
      reqd: 1,
    },

    {
      fieldname: "view_mode",
      label: __("View Mode"),
      fieldtype: "Select",
      options: [
        { label: __("Party Number"), value: "Party Number" },
        { label: __("Active Accounts"), value: "Active Accounts" },
        { label: __("Dormant Accounts"), value: "Dormant Accounts" },
        { label: __("High Debit Balance"), value: "High Debit Balance" },
        { label: __("Zero Balance Accounts"), value: "Zero Balance Accounts" },
      ],
      default: "Party Number",
      on_change: function () {
        let view_mode = frappe.query_report.get_filter_value("view_mode");

        // Toggle from_date visibility
        let from_date_filter = frappe.query_report.get_filter("from_date");
        if (from_date_filter) {
          if (
            view_mode === "Active Accounts" ||
            view_mode === "Dormant Accounts"
          ) {
            from_date_filter.df.hidden = 0;
            from_date_filter.refresh();
          } else {
            from_date_filter.df.hidden = 1;
            from_date_filter.refresh();
          }
        }

        // Toggle debit_threshold visibility
        let threshold_filter =
          frappe.query_report.get_filter("debit_threshold");
        if (threshold_filter) {
          if (view_mode === "High Debit Balance") {
            threshold_filter.df.hidden = 0;
            threshold_filter.refresh();
          } else {
            threshold_filter.df.hidden = 1;
            threshold_filter.refresh();
          }
        }

        frappe.query_report.refresh();
      },
    },

    {
      fieldname: "from_date",
      label: __("Activity From Date"),
      fieldtype: "Date",
      default: frappe.datetime.add_days(frappe.datetime.get_today(), -365),
      hidden: 1,
    },

    {
      fieldname: "debit_threshold",
      label: __("Debit Threshold"),
      fieldtype: "Currency",
      hidden: 1,
    },

    {
      fieldname: "arrange_balances",
      label: __("Balances Arranged:"),
      fieldtype: "Select",
      options: [
        {
          label: __("horizontally Arrangement"), //افقيا
          value: "Horizontal",
        },
        {
          label: __("Sequential Arrangement"),
          value: "Sequential Arrangement",
        },
      ],
      default: "Horizontal",
    },

    {
      fieldname: "party_analytic_accounting",
      label: __("Party Analytic Accounting"),
      fieldtype: "MultiSelectList",
      options: "Party Analytic Accounting",
      get_data: function (txt) {
        if (frappe.query_report.get_filter_value("is_group")) return [];
        let party_master = frappe.query_report.get_filter_value("party_master");
        if (party_master.lenght > 1 || !party_master) return [];
        return frappe.db.get_link_options("Party Analytic Accounting", txt, {
          party_master: party_master[0],
        });
      },
    },
    {
      fieldname: "cost_center",
      label: __("Cost Center"),
      fieldtype: "MultiSelectList",
      options: "Cost Center",
      get_data: function (txt) {
        return frappe.db.get_link_options("Cost Center", txt, {
          company: frappe.query_report.get_filter_value("company"),
        });
      },
    },
    {
      fieldname: "project",
      label: __("Project"),
      fieldtype: "MultiSelectList",
      options: "Project",
      get_data: function (txt) {
        return frappe.db.get_link_options("Project", txt, {
          company: frappe.query_report.get_filter_value("company"),
        });
      },
    },

    {
      fieldname: "party_account",
      label: __("Receivable Account"),
      fieldtype: "Link",
      options: "Account",
      get_query: () => {
        var company = frappe.query_report.get_filter_value("company");
        return {
          filters: {
            company: company,
            account_type: "Receivable",
            is_group: 0,
          },
        };
      },
    },
    {
      fieldname: "party_type",
      label: __("Party Type"),
      fieldtype: "MultiSelectList",
      options: [],
      get_data: (txt) => {
        let default_option = [
          {
            value: "All",
            label: __("All"),
            description: __(
              "Default to show accounting entries for all Party Types under Party Master"
            ),
          },
        ];

        let dynamic_options = Object.keys(
          frappe.boot.party_account_types || {}
        ).map((key) => ({
          value: key,
          label: __(key),
          description: __("only accounting entries for {0} will be shown", [
            __(key),
          ]),
        }));

        return default_option.concat(dynamic_options);
      },
    },
    {
      fieldname: "presentation_currency",
      label: __("Currency"),
      fieldtype: "MultiSelectList",
      options: erpnext.get_presentation_currency_list().map((currency) => ({
        value: currency,
        description: "",
        label: currency === "" ? __("For All Currencies") : __(currency),
      })),
    },

    {
      fieldname: "sales_partner",
      label: __("Sales Partner"),
      fieldtype: "Link",
      options: "Sales Partner",
    },
    {
      fieldname: "sales_person",
      label: __("Sales Person"),
      fieldtype: "Link",
      options: "Sales Person",
    },
    {
      fieldname: "territory",
      label: __("Territory"),
      fieldtype: "Link",
      options: "Territory",
    },
    {
      fieldname: "is_group",
      label: __("For Group"),
      fieldtype: "Check",
      default: 1,

      on_change: function () {
        frappe.query_report.set_filter_value("party", []);
      },
    },

    {
      fieldname: "in_company_currency",
      label: __("Add Columns In Company Currency"),
      fieldtype: "Check",
      default: 0,
    },

    {
      fieldname: "show_sales_person",
      label: __("Show Sales Person"),
      fieldtype: "Check",
    },

    {
      fieldname: "for_revaluation_journals",
      label: __("Revaluation Journals"),
      fieldtype: "Check",
    },
  ],
  formatter: function (value, row, column, data, default_formatter) {
    let currency;
    if (column.fieldtype === "Currency") {
      let currency;
      if (
        frappe.query_report.get_filter_value("arrange_balances") !==
        "Horizontal" &&
        column.fieldname !== "balance_in_cc"
      ) {
        currency = data.currency;
      } else {
        currency = column.options;
      }
      const formatted = format_currency(value, currency);

      if (value > 0) {
        return `<span style="color:red;">&#9650;</span> <b>${formatted}</b>`;
      } else if (value < 0) {
        return `<span style="color:green;">&#9660;</span> ${formatted}`;
      } else {
        return "0";
      }
    }

    if (column.fieldname === "party_type" || column.fieldname === "status") {
      return __(value);
    }
    return default_formatter(value, row, column, data);
  },

  onload: function (report) {
    report.page.add_inner_button(
      __("Party Account Statement"),
      function () {
        var filters = report.get_values();
        frappe.set_route("query-report", "Party Account Statement", {
          company: filters.company,
          party_master: filters.party_master,
        });
      },
      __("View")
    );
    report.page.add_inner_button(
      __("Chronological Party Ledger"),
      function () {
        var filters = report.get_values();
        frappe.set_route("query-report", "Chronological Party Ledger", {
          company: filters.company,
          party_master: filters.party_master,
        });
      },
      __("View")
    );
  },
};

erpnext.utils.add_dimensions("Party Account Balances", 9);
