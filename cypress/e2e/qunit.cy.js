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
		cy.wrap(root).find("#qunit-testresult", { timeout: 180000 }).should("contain", "completed");
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

	const assertRunnerFromCurrentPage = () => {
		return cy.get("body", { timeout: 120000 }).then(($body) => {
			if ($body.find("#qunit-testresult").length) {
				assertQUnitPassed($body);
				return true;
			}

			if ($body.find("iframe").length) {
				assertQUnitFromIframe();
				return true;
			}

			return false;
		});
	};

	it("runs the QUnit suite for the UPH app", () => {
		login();

		const candidates = [
			"/app/tests?app=uph",
			"/assets/frappe/js/test_runner.html?app=uph",
			"/assets/frappe/js/test_runner.html",
		];

		const tryCandidate = (index = 0) => {
			const candidate = candidates[index];
			cy.visit(candidate, { failOnStatusCode: false });

			assertRunnerFromCurrentPage().then((hasRunner) => {
				if (hasRunner) {
					return;
				}

				if (index >= candidates.length - 1) {
					throw new Error(`QUnit runner not found in known URLs: ${candidates.join(", ")}`);
				}

				tryCandidate(index + 1);
			});
		};

		tryCandidate();
	});
});
