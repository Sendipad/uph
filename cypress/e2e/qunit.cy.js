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

	const assertQUnitFromIframe = () => {
		cy.get("iframe", { timeout: 180000 })
			.first()
			.its("0.contentDocument.body")
			.should("not.be.empty")
			.then((iframeBody) => {
				assertQUnitPassed(iframeBody);
			});
	};

	it("runs the QUnit suite for the UPH app", () => {
		login();
		cy.visit("/app/tests?app=uph");

		cy.get("body", { timeout: 120000 }).then(($body) => {
			if ($body.find("#qunit-testresult").length) {
				assertQUnitPassed($body);
				return;
			}

			if ($body.find("iframe").length) {
				assertQUnitFromIframe();
				return;
			}

			cy.get("#qunit-testresult, iframe", { timeout: 180000 }).then(($runner) => {
				if ($runner.filter("#qunit-testresult").length) {
					cy.get("body").then(assertQUnitPassed);
					return;
				}

				assertQUnitFromIframe();
			});
		});
	});
});
