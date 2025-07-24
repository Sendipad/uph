frappe.ui.form.on('Rule', {
  refresh(frm) {
    // placeholder sections in Rule doctype for mounting
    if (frm.fields_dict.conditions_html)
      $(frm.fields_dict.conditions_html.wrapper).html('<div id="rule-conditions"></div>');
    if (frm.fields_dict.actions_html)
      $(frm.fields_dict.actions_html.wrapper).html('<div id="rule-actions"></div>');
    frappe.require('/assets/uph/js/vue_loader.js');
  }
});
