frappe.ui.form.on("Party Issue", {
    refresh(frm) {
        frm.trigger("render_details");
        frm.trigger("setup_buttons");
        frm.trigger("setup_readonly");
    },

    setup_buttons(frm) {
        if (frm.doc.status === "Open") {
            frm.add_custom_button(__("Resolve"), () => {
                frm.set_value("status", "Resolved");
                frm.save();
            }, __("Actions"));

            frm.add_custom_button(__("Ignore"), () => {
                frappe.prompt([
                    {
                        label: __("Reason for Ignoring"),
                        fieldname: "reason",
                        fieldtype: "Small Text",
                        reqd: 1
                    }
                ], (values) => {
                    frm.set_value("status", "Ignored");
                    frm.set_value("dismiss_reason", values.reason);
                    frm.save();
                }, __("Ignore Issue"), __("Submit"));
            }, __("Actions"));
        }
    },

    setup_readonly(frm) {
        if (["Resolved", "Ignored"].includes(frm.doc.status)) {
            frm.set_read_only();
        }
    },

    render_details(frm) {
        if (frm.doc.details_json) {
            try {
                let details = JSON.parse(frm.doc.details_json);
                let html = `<div class="details-container">
					<table class="table table-bordered table-condensed" style="background-color: var(--bg-light-gray);">
						<thead>
							<tr>
								<th>${__("Property")}</th>
								<th>${__("Value")}</th>
							</tr>
						</thead>
						<tbody>`;

                for (let key in details) {
                    let val = details[key];
                    if (typeof val === 'object') {
                        val = JSON.stringify(val);
                    }
                    html += `<tr>
						<td><strong>${frappe.model.unscrub(key)}</strong></td>
						<td>${val}</td>
					</tr>`;
                }

                html += `</tbody></table></div>`;
                frm.set_df_property("details_html", "options", html);
                frm.refresh_field("details_html");
            } catch (e) {
                console.error("Failed to parse details_json", e);
            }
        } else {
            frm.set_df_property("details_html", "options", `<div class="text-muted">${__("No additional details available.")}</div>`);
        }
    }
});
