//file: apps/uph/uph/public/js/rule_builder/utils.js
import { reactive, computed } from "vue";

export const serviceUIConfigs = reactive({});
const metaCache = {};

export function registerServiceUIConfig(serviceType, config) {
	serviceUIConfigs[serviceType] = config;
}
export async function loadDoctypeFields(
	doctype,
	{ excludeFieldnames = new Set(), excludeFieldtypes = new Set() } = {},
) {
	try {
		// Ensure doctype meta is loaded
		await frappe.model.with_doctype(doctype);

		const fields = frappe.meta.get_docfields(doctype);
		if (!Array.isArray(fields)) {
			throw new Error(`Expected array of fields from get_docfields for "${doctype}"`);
		}

		// Apply filters
		return fields.filter(
			(f) => !excludeFieldnames.has(f.fieldname) && !excludeFieldtypes.has(f.fieldtype),
		);
	} catch (err) {
		console.error(`Failed to load fields for doctype "${doctype}":`, err);
		return [];
	}
}
export async function getServiceUIConfig(serviceType) {
	if (!serviceType) return {};

	if (!serviceUIConfigs[serviceType]) {
		try {
			const { message } = await frappe.call({
				method: "uph.hub.utils.service.get_service_ui_config",
				args: { service_type: serviceType },
			});
			registerServiceUIConfig(serviceType, message || {});
		} catch (err) {
			console.warn("Failed to fetch service UI config", err);
			registerServiceUIConfig(serviceType, {});
		}
	}
	return serviceUIConfigs[serviceType];
}

export function useServiceUIConfig(ruleServiceTypeRef) {
	return computed(() => {
		const type = ruleServiceTypeRef.value;
		if (!type) return {};
		return serviceUIConfigs[type] || {};
	});
}

export function getMergedFields(configFields = [], fallbackFields = []) {
	const map = Object.fromEntries(fallbackFields.map((f) => [f.fieldname, f]));
	return configFields.map((f) => ({
		...(map[f.fieldname] || {}), // fallback first
		...f, // config overrides fallback
	}));
}
export function getFinalFields(config = {}, metaFields = [], mode = "full") {
	const configFields = config.fields || [];
	const hiddenFields = new Set(config.fields_hidden || []);
	const compactFieldnames = (config.vue?.grid || []).filter(Boolean);

	const metaMap = Object.fromEntries(metaFields.map((f) => [f.fieldname, { ...f }]));
	const configMap = Object.fromEntries(configFields.map((f) => [f.fieldname, { ...f }]));

	// Final fieldnames depends on layout mode
	const finalFieldnames = new Set(
		mode === "compact"
			? compactFieldnames
			: [
					...new Set([
						...metaFields.map((f) => f.fieldname),
						...configFields.map((f) => f.fieldname),
					]),
				],
	);

	// Merge each field
	const merged = [];
	for (const fieldname of finalFieldnames) {
		if (hiddenFields.has(fieldname)) continue;

		const base = metaMap[fieldname] || {};
		const override = configMap[fieldname] || {};
		merged.push({ ...base, ...override });
	}
	return merged;
}

window.__ =
	window.__ ||
	function (s) {
		return s;
	};

export const fieldCache = new Map();
const MAX_CACHE_SIZE = 100;

function getDoctypeCacheKey(documentType) {
	return Array.isArray(documentType) ? documentType.sort().join("|") : documentType;
}

export function safeFrappeUtils() {
	return {
		icon: (icon, size) => {
			return frappe?.utils?.icon?.(icon, size) || `<span>${icon}</span>`;
		},
	};
}

export async function loadFieldOptions(documentType) {
	// Normalize input: always use sorted unique array
	const normalizedTypes = Array.isArray(documentType)
		? [...new Set(documentType)].sort()
		: [documentType];

	const key = normalizedTypes.join("|");

	// Return cached value if available
	if (fieldCache.has(key)) {
		return fieldCache.get(key);
	}

	try {
		let method, args;
		const isMultiDocType = normalizedTypes.length > 1;

		if (isMultiDocType) {
			method = "uph.hub.utils.field.get_common_fields_in_doctypes";
			args = { doctypes: JSON.stringify(normalizedTypes) };
		} else {
			method = "uph.hub.utils.field.get_field_options";
			args = { doctype: normalizedTypes[0] };
		}

		const { message } = await frappe.call({
			method,
			args,
			freeze: false,
			async: true,
		});

		const result = Array.isArray(message) ? message : [];
		fieldCache.set(key, result);
		return result;
	} catch (err) {
		fieldCache.set(key, []);
		frappe.log_error("Field options load error", err);
		return [];
	}
}

// Cache cleanup function
export function clearFieldCache() {
	fieldCache.clear();
}

export async function getFieldMeta(doctype) {
	if (!metaCache[doctype]) {
		await frappe.model.with_doctype(doctype);
		metaCache[doctype] = frappe.get_meta(doctype);
	}
	return metaCache[doctype];
}

export async function getDocFieldOptions(doctype, fieldname) {
	await frappe.model.with_doctype(doctype);
	const meta = frappe.get_meta(doctype);
	const field = meta.fields.find((df) => df.fieldname === fieldname);

	if (field && field.options) {
		return field.options.split("\n").filter((opt) => opt.trim());
	}

	return [];
}

export function getCachedField(documentType, fieldPath) {
	const key = getDoctypeCacheKey(documentType);
	const list = field_path_cache(key);
	return list?.find((f) => f.value === fieldPath) || null;
}

export function getCachedFieldType(documentType, fieldPath) {
	return getCachedField(documentType, fieldPath)?.fieldtype || "Data";
}

export function hasCachedField(documentType, fieldPath) {
	return !!getCachedField(documentType, fieldPath);
}

export function getCachedFieldsForDoctype(documentType) {
	const key = getDoctypeCacheKey(documentType);
	return fieldCache.get(key) || [];
}
// utils/formatValue.ts
/**
 * Safe get: supports nested keys like 'meta.label'
 */
function get(obj, path, fallback = "[?]") {
	if (!obj || typeof obj !== "object") return fallback;
	return path.split(".").reduce((acc, part) => acc && acc[part], obj) ?? fallback;
}

/**
 * Format a value based on fieldtype
 * @param {*} value - the raw value (string, number, object, etc.)
 * @param {Object} field - a DocField object with at least `fieldtype` and optional `options`, `precision`
 * @param {Object} opts - optional: locale, currency override
 * @returns {string} formatted value
 */
export function formatValue(value, field, opts = {}) {
	if (value == null || value === "") return "";

	switch (field.fieldtype) {
		case "Data":
		case "Text":
		case "Small Text":
		case "Long Text":
		case "Code":
		case "Read Only":
			return String(value);

		case "Int":
		case "Float":
		case "Percent":
			return Number(value).toLocaleString(opts.locale, {
				minimumFractionDigits: field.precision ?? (field.fieldtype === "Percent" ? 2 : 0),
				maximumFractionDigits: field.precision ?? 4,
			});

		case "Currency": {
			const currency = opts.currency || field.options || "USD";
			return new Intl.NumberFormat(opts.locale, {
				style: "currency",
				currency,
				minimumFractionDigits: field.precision ?? 2,
			}).format(Number(value));
		}

		case "Date":
			return new Date(value).toLocaleDateString(opts.locale);

		case "Datetime":
			return new Date(value).toLocaleString(opts.locale);

		case "Time":
			try {
				return new Date(`1970-01-01T${value}Z`).toLocaleTimeString(opts.locale, {
					hour: "2-digit",
					minute: "2-digit",
				});
			} catch {
				return String(value);
			}

		case "Check":
		case "Boolean":
			return value ? "✔️" : "✖️";

		case "Select":
			return String(value);

		case "Link":
		case "Dynamic Link":
			return String(value);

		case "Rating":
			return "★".repeat(value) + "☆".repeat(5 - value);

		case "JSON": {
			let parsed;

			try {
				parsed = typeof value === "string" ? JSON.parse(value) : value;
			} catch (e) {
				return "[Invalid JSON]";
			}

			const keyPath = field.options || "label";

			// Case: list of lists
			if (Array.isArray(parsed) && parsed.every((item) => Array.isArray(item))) {
				const formattedGroups = parsed.map((group, i) => {
					if (i === 0) {
						// First group — plain strings
						return group.map((str) => String(str)).join(", ");
					} else {
						// Other groups — format objects
						return group
							.map((obj) => (typeof obj === "object" ? get(obj, keyPath) : String(obj)))
							.join(" > ");
					}
				});

				return formattedGroups.join(" | ");
			}

			// Case: list of objects
			if (Array.isArray(parsed)) {
				return parsed
					.map((item) => (typeof item === "object" ? get(item, keyPath) : String(item)))
					.join(" > ");
			}

			// Case: plain object
			if (typeof parsed === "object") {
				return Object.entries(parsed)
					.map(([k, v]) => `${k}: ${v}`)
					.join(", ");
			}

			return String(parsed);
		}

		default:
			return String(value);
	}
}

// Add this function for ID generation
export function generateUniqueId() {
	return frappe.utils.get_random(8);
}

export function evaluate_depends_on_value(expression, doc, parent = {}) {
	if (!expression || !doc) return false;

	let result = false;

	const context = { doc, parent };

	try {
		switch (typeof expression) {
			case "boolean":
				result = expression;
				break;

			case "function":
				result = expression(doc, parent);
				break;

			case "string":
				if (expression.startsWith("eval:")) {
					const code = expression.slice(5).trim();
					const fn = new Function("doc", "parent", `return (${code})`);
					result = fn(context.doc, context.parent);
				} else {
					const value = doc[expression];
					result = Array.isArray(value) ? value.length > 0 : !!value;
				}
				break;

			default:
				console.warn("[depends_on] Unsupported expression type:", typeof expression);
		}
	} catch (e) {
		console.warn("[evaluate_depends_on_value] Evaluation failed:", {
			expression,
			doc,
			parent,
			error: e,
		});
		result = false;
	}

	return !!result;
}

frappe.provide("uph.hub");

uph.hub.field_options = {
	loadFieldOptions,
	getCachedField,
	getCachedFieldType,
	hasCachedField,
	getCachedFieldsForDoctype, // ✅ ADD THIS
	fieldCache,
};

uph.hub.serviceRegistry = {
	register: registerServiceUIConfig,
	get: getServiceUIConfig,
};
