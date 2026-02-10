describe("UPH QUnit Tests", () => {
	const login = () => {
		const user = Cypress.env("CY_LOGIN_USER") || "Administrator";
		const password = Cypress.env("CY_LOGIN_PASSWORD") || "admin";

		return cy.request("POST", "/api/method/login", {
			usr: user,
			pwd: password,
		});
	};

	it("runs the QUnit suite for the UPH app", () => {
		login();

		cy.visit("/app/tests?app=uph");
		cy.get("#qunit-testresult", { timeout: 120000 }).should("contain", "completed");
		cy.get("#qunit-testresult .failed").should("contain", "0");
	});
});
