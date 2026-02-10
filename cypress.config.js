const { defineConfig } = require("cypress");

module.exports = defineConfig({
	video: false,
	screenshotOnRunFailure: false,
	e2e: {
		baseUrl: process.env.CYPRESS_baseUrl || "http://localhost:8000",
		specPattern: "cypress/e2e/**/*.cy.js",
		supportFile: false,
		defaultCommandTimeout: 30000,
		pageLoadTimeout: 120000,
	},
});
