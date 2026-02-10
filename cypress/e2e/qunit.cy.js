describe("UPH Frontend Utility Tests", () => {
	const login = () => {
		const user = Cypress.env("CY_LOGIN_USER") || "Administrator";
		const password = Cypress.env("CY_LOGIN_PASSWORD") || "admin";

		return cy.request("POST", "/api/method/login", {
			usr: user,
			pwd: password,
		});
	};

	const openDesk = () => {
		cy.visit("/app", { failOnStatusCode: false });
		cy.window({ timeout: 120000 }).should((win) => {
			expect(win.frappe).to.exist;
			expect(win.uph).to.exist;
			expect(win.uph.party).to.exist;
		});
	};

	beforeEach(() => {
		login();
		openDesk();
	});

	it("caches party type rules and handles empty responses", () => {
		cy.window().then((win) => {
			win.uph.party_type_pm_rules = {};
			const originalCall = win.frappe.call;
			let callCount = 0;

			win.frappe.call = ({ callback }) => {
				callCount += 1;
				callback({
					message: {
						Customer: { allowed: 1, reqd: 1 },
						Supplier: { allowed: 0, reqd: 0 },
					},
				});
			};

			return new Cypress.Promise((resolve, reject) => {
				win.uph.get_party_type_party_master_rules("Customer", (rules) => {
					try {
						expect(callCount).to.equal(1);
						expect(rules).to.deep.equal({ allowed: 1, reqd: 1 });

						win.uph.get_party_type_party_master_rules("Supplier", (cachedRules) => {
							try {
								expect(callCount).to.equal(1);
								expect(cachedRules).to.deep.equal({ allowed: 0, reqd: 0 });

								win.frappe.call = ({ callback }) => callback({ message: null });
								win.uph.party_type_pm_rules = {};
								win.uph.get_party_type_party_master_rules("Customer", (emptyRules) => {
									try {
										expect(emptyRules).to.equal(null);
										win.frappe.call = originalCall;
										resolve();
									} catch (error) {
										win.frappe.call = originalCall;
										reject(error);
									}
								});
							} catch (error) {
								win.frappe.call = originalCall;
								reject(error);
							}
						});
					} catch (error) {
						win.frappe.call = originalCall;
						reject(error);
					}
				});
			});
		});
	});

	it("covers UPH party utility helpers", () => {
		cy.window().then((win) => {
			const sales = win.uph.party.get_fieldnames({ doc: { doctype: "Sales Invoice" } });
			expect(sales).to.deep.equal({
				party_type: "Customer",
				party_fieldname: "customer",
				default_role_fieldname: "default_customer",
			});

			const filters = win.uph.party.pm_base_filter({ doc: { doctype: "Sales Invoice" } });
			expect(filters).to.deep.equal({
				doctype: "Sales Invoice",
				reference_doctype: "Sales Invoice",
				disabled: 0,
				is_group: 0,
				party_type: "Customer",
			});

			const frm = {
				fields_dict: { party_analytic_accounting: {} },
				toggle_reqd(fieldname, value) {
					this.lastToggle = { fieldname, value };
				},
			};
			win.uph.party.finalize_pm_details(frm, { enforce_party_analytic_accounting_selection: true });
			expect(frm.lastToggle).to.deep.equal({
				fieldname: "party_analytic_accounting",
				value: true,
			});

			const fields = win.uph.party.get_dialog_field(
				{ get_default_partyRole: false },
				{ party_type_roles: ["Customer"], parties: [{ name: "CUST-0001", currency: "USD" }] },
				{ party_type: "Customer", isdynamic: 0 },
			);
			const partyField = fields.find((field) => field.fieldname === "party");
			const partyTypeField = fields.find((field) => field.fieldname === "party_type");
			expect(partyField.options).to.deep.equal(["CUST-0001 (USD)"]);
			expect(partyTypeField.hidden).to.equal(true);

			const query = win.erpnext.queries.get_filtered_dimensions(
				{ doctype: "Sales Invoice", party_master: "PM-001", customer: "CUST-0001" },
				null,
				"party_analytic_accounting",
				"Test Company",
			);
			expect(query).to.deep.equal({
				query: "uph.party.controllers.queries.get_party_analytic_accounting_filtered",
				filters: {
					party_master: "PM-001",
					party: "CUST-0001",
					company: "Test Company",
				},
			});
		});
	});
});
