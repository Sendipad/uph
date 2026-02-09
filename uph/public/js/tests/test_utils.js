QUnit.module("UPH Utils", (hooks) => {
	let originalCall;

	hooks.beforeEach(() => {
		if (!window.__) {
			window.__ = (message) => message;
		}
		if (!window.uph) {
			window.uph = {};
		}
		uph.party_type_pm_rules = {};
		originalCall = frappe.call;
	});

	hooks.afterEach(() => {
		frappe.call = originalCall;
	});

	QUnit.test("get_party_type_party_master_rules caches rules by party type", (assert) => {
		const done = assert.async();
		let callCount = 0;
		frappe.call = ({ callback }) => {
			callCount += 1;
			callback({
				message: {
					Customer: { allowed: 1, reqd: 1 },
					Supplier: { allowed: 0, reqd: 0 },
				},
			});
		};

		uph.get_party_type_party_master_rules("Customer", (rules) => {
			assert.strictEqual(callCount, 1, "fetches rules on first call");
			assert.deepEqual(rules, { allowed: 1, reqd: 1 }, "returns the requested rules");

			uph.get_party_type_party_master_rules("Supplier", (cachedRules) => {
				assert.strictEqual(callCount, 1, "uses cached rules on subsequent calls");
				assert.deepEqual(cachedRules, { allowed: 0, reqd: 0 }, "returns cached rules");
				done();
			});
		});
	});

	QUnit.test("get_party_type_party_master_rules handles empty responses", (assert) => {
		const done = assert.async();
		frappe.call = ({ callback }) => {
			callback({ message: null });
		};

		uph.get_party_type_party_master_rules("Customer", (rules) => {
			assert.strictEqual(rules, null, "returns null when no rules are provided");
			done();
		});
	});
});
