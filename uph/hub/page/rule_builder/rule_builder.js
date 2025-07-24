frappe.pages["rule-builder"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Rule Builder",
		single_column: true,
	});

	// Create container with debug styles
	const container = $(`
    <div id="rule-builder-container" style="
      padding: 20px;
      background: #f8f9fa;
      min-height: calc(100vh - 50px);
      border: 3px solid green;
    ">
      <div id="rule-builder-app" style="
        border: 2px dashed #0d6efd;
        padding: 20px;
        background: white;
        min-height: 300px;
      ">
        <p id="status">Initializing...</p>
      </div>
    </div>
  `);

	$(page.body).empty().append(container);

	// Load Vue directly first
	const loadVue = new Promise((resolve) => {
		if (typeof Vue !== "undefined") return resolve();

		const script = document.createElement("script");
		script.src = "https://unpkg.com/vue@3/dist/vue.global.prod.js";
		script.onload = resolve;
		document.head.appendChild(script);
	});

	// Load app script
	const loadApp = new Promise((resolve, reject) => {
		const script = document.createElement("script");
		script.src = frappe.urllib.get_full_url(
			"/assets/uph/js/rule-builder/rule-builder.js?" + new Date().getTime(),
		);
		script.onload = resolve;
		script.onerror = reject;
		document.head.appendChild(script);
	});

	// Update status
	$("#status").text("Loading Vue...");

	loadVue
		.then(() => {
			$("#status").text("Vue loaded, loading app...");
			return loadApp;
		})
		.then(() => {
			$("#status").text("Assets loaded, mounting...");

			if (typeof window.mountRuleBuilder === "function") {
				// Create observer to ensure element exists
				const observer = new MutationObserver(() => {
					const el = document.getElementById("rule-builder-app");
					if (el) {
						observer.disconnect();
						window.mountRuleBuilder("rule-builder-app");
						$("#status").text("App mounted!");
					}
				});

				observer.observe(document.body, {
					childList: true,
					subtree: true,
				});
			} else {
				throw new Error("mountRuleBuilder function not found");
			}
		})
		.catch((error) => {
			console.error("Load error:", error);
			$("#rule-builder-app").html(`
        <div class="alert alert-danger">
          <h4>Load Error</h4>
          <p>${error.message}</p>
          <pre>${error.stack}</pre>
        </div>
      `);
		});
};
