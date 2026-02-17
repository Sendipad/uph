module.exports = {
	video: false,
	screenshotOnRunFailure: true,
	e2e: {
		baseUrl: process.env.CYPRESS_baseUrl || "http://localhost:8000",
		specPattern: "cypress/e2e/**/*.cy.js",
		supportFile: false,
		defaultCommandTimeout: 30000,
		pageLoadTimeout: 120000,
	},
};
