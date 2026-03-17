import frappe
from uph.install.after_install import after_install


def execute():
	after_install()
	frappe.db.commit()
