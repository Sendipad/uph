frappe.listview_settings['Party Issue'] = {
    hide_name_column: true,
    get_indicator(doc) {
        const status_colors = {
            "Open": "orange",
            "Under Review": "blue",
            "Resolved": "green",
            "Ignored": "gray"
        };
        return [__(doc.status), status_colors[doc.status] || "gray", "status,=," + doc.status];
    },
    formatters: {
        severity(val) {
            const colors = {
                "Low": "blue",
                "Medium": "green",
                "High": "orange",
                "Critical": "red"
            };
            return `<span class="indicator-pill ${colors[val] || "gray"}">${__(val)}</span>`;
        },
        reference_name(val, df, doc) {
            if (doc.reference_doctype && val) {
                return `<a href="/app/${frappe.router.slug(doc.reference_doctype)}/${val}" class="text-muted font-weight-bold">${val}</a>`;
            }
            return val;
        },
        party_secondary(val, df, doc) {
            if (val) {
                return `<a href="/app/party-master/${val}" class="text-muted font-weight-bold">${val}</a>`;
            }
            return val;
        }
    }
};
