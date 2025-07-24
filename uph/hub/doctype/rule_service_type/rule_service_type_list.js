frappe.listview_settings["Rule Service Type"] = {
  onload: function (listview) {
    listview.page.clear_primary_action(); // Removes the "New" button
  }
};
