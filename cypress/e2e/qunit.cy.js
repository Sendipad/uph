describe("UPH QUnit Tests", () => {
	const login = () => {
		const user = Cypress.env("CY_LOGIN_USER") || "Administrator";
		const password = Cypress.env("CY_LOGIN_PASSWORD") || "admin";

		return cy.request("POST", "/api/method/login", {
			usr: user,
			pwd: password,
		});
	};

	const assertQUnitPassed = (root) => {
		cy.wrap(root)
			.find("#qunit-testresult", { timeout: 180000 })
			.should("contain", "completed");
		cy.wrap(root).find("#qunit-testresult .failed").should("contain", "0");
	};

	it("runs the QUnit suite for the UPH app", () => {
		login();
		cy.visit("/app/tests?app=uph");

		cy.get("body", { timeout: 60000 }).then(($body) => {
			if ($body.find("#qunit-testresult").length) {
				assertQUnitPassed($body);
				return;
			}

			cy.get("iframe", { timeout: 60000 })
				.first()
				.its("0.contentDocument.body")
				.should("not.be.empty")
				.then((iframeBody) => {
					assertQUnitPassed(iframeBody);
				});
		});
	});
});
