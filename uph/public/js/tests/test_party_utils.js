QUnit.module("UPH Party Utils", (hooks) => {
	hooks.beforeEach(() => {
		if (!window.__) {
			window.__ = (message) => message;
		}
	});

	QUnit.test("get_fieldnames maps party fields by doctype", (assert) => {
		if (!window.uph?.party) {
			assert.ok(false, "uph.party is not available");
			return;
		}

		const sales = uph.party.get_fieldnames({ doc: { doctype: "Sales Invoice" } });
		assert.deepEqual(
			sales,
			{
				party_type: "Customer",
				party_fieldname: "customer",
				default_role_fieldname: "default_customer",
			},
			"returns sales party mapping"
		);

		const purchase = uph.party.get_fieldnames({ doc: { doctype: "Purchase Order" } });
		assert.deepEqual(
			purchase,
			{
				party_type: "Supplier",
				party_fieldname: "supplier",
				default_role_fieldname: "default_supplier",
			},
			"returns purchase party mapping"
		);

		const payment = uph.party.get_fieldnames({
			doc: { doctype: "Payment Entry", party_type: "Employee" },
		});
		assert.deepEqual(
			payment,
			{ party_type: "Employee", party_fieldname: "party", isdynamic: 1 },
			"returns dynamic payment entry mapping"
		);
	});

	QUnit.test("pm_base_filter includes party type and defaults", (assert) => {
		if (!window.uph?.party) {
			assert.ok(false, "uph.party is not available");
			return;
		}

		const frm = { doc: { doctype: "Sales Invoice" } };
		const filters = uph.party.pm_base_filter(frm);
		assert.deepEqual(
			filters,
			{
				doctype: "Sales Invoice",
				reference_doctype: "Sales Invoice",
				disabled: 0,
				is_group: 0,
				party_type: "Customer",
			},
			"builds the base party master filter"
		);
	});

	QUnit.test("finalize_pm_details toggles analytic accounting requirement", (assert) => {
		if (!window.uph?.party) {
			assert.ok(false, "uph.party is not available");
			return;
		}

		const frm = {
			fields_dict: { party_analytic_accounting: {} },
			toggle_reqd(fieldname, value) {
				this.lastToggle = { fieldname, value };
			},
		};

		uph.party.finalize_pm_details(frm, {
			enforce_party_analytic_accounting_selection: true,
		});
		assert.deepEqual(
			frm.lastToggle,
			{ fieldname: "party_analytic_accounting", value: true },
			"enforces requirement when enabled"
		);

		uph.party.finalize_pm_details(frm, {
			enforce_party_analytic_accounting_selection: false,
		});
		assert.deepEqual(
			frm.lastToggle,
			{ fieldname: "party_analytic_accounting", value: false },
			"removes requirement when disabled"
		);
	});

	QUnit.test("get_dialog_field formats party options with currency", (assert) => {
		if (!window.uph?.party) {
			assert.ok(false, "uph.party is not available");
			return;
		}

		const pmDetails = {
			party_type_roles: ["Customer"],
			parties: [{ name: "CUST-0001", currency: "USD" }],
		};

		const fields = uph.party.get_dialog_field({ get_default_partyRole: false }, pmDetails, {
			party_type: "Customer",
			isdynamic: 0,
		});

		const partyField = fields.find((field) => field.fieldname === "party");
		const partyTypeField = fields.find((field) => field.fieldname === "party_type");

		assert.deepEqual(
			partyField.options,
			["CUST-0001 (USD)"],
			"includes currency in party option labels"
		);
		assert.strictEqual(
			partyTypeField.hidden,
			true,
			"hides party type when only one option exists"
		);
	});

	QUnit.test("get_filtered_dimensions targets party master analytics", (assert) => {
		if (!window.erpnext?.queries?.get_filtered_dimensions) {
			assert.ok(false, "erpnext.queries.get_filtered_dimensions is not available");
			return;
		}

		const result = erpnext.queries.get_filtered_dimensions(
			{ doctype: "Sales Invoice", party_master: "PM-001", customer: "CUST-0001" },
			null,
			"party_analytic_accounting",
			"Test Company"
		);

		assert.deepEqual(
			result,
			{
				query: "uph.party.controllers.queries.get_party_analytic_accounting_filtered",
				filters: {
					party_master: "PM-001",
					party: "CUST-0001",
					company: "Test Company",
				},
			},
			"returns the party master analytics query"
		);
	});
});
