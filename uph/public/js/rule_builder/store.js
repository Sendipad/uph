import { defineStore } from "pinia";
import { computed, ref, reactive, watch, toRaw, nextTick } from "vue";
import { generateUniqueId, useServiceUIConfig, getFinalFields } from "./utils";
import { useDebouncedRefHistory, onKeyDown } from "@vueuse/core";

export const useRuleBuilderStore = defineStore("ruleBuilder", () => {
	const frm = ref(null);
	const doc = ref({});
	const conditions = ref([]);
	const actions = ref([]);
	const collapsed = reactive({});
	const focusedConditionId = ref(null);
	const dirty = ref(false);
	const isLoaded = ref(false);
	const layoutMode = ref("compact");

	const originalDocSnapshot = ref(null);
	const originalConditions = ref([]);
	const originalActions = ref([]);

	const serviceUIConfig = useServiceUIConfig(computed(() => doc.value?.rule_service_type));

	const history = useDebouncedRefHistory([conditions, actions], {
		deep: true,
		dump: (v) => JSON.stringify(toRaw(v)),
		parse: (v) => {
			try {
				return JSON.parse(v);
			} catch (e) {
				console.warn("Failed to parse history snapshot", e);
				return [];
			}
		},
	});

	const conditionsMap = computed(() =>
		Object.fromEntries(conditions.value.map((c) => [c.condition_id, c])),
	);

	const rootConditions = computed(() =>
		conditions.value.filter((c) => !c.parent_condition_id || c.parent_condition_id === "ROOT"),
	);

	const childConditions = (parentId) =>
		conditions.value.filter((c) => c.parent_condition_id === parentId);

	const mergedConditionFields = computed(() => {
		const getFields = uph?.hub?.field_options?.getCachedFieldsForDoctype;
		if (typeof getFields !== "function") return [];
		const meta = getFields("Rule Condition") || [];
		const config = serviceUIConfig.value?.["Rule Condition"] || {};
		return getFinalFields(config, meta, layoutMode.value);
	});

	function deepClone(obj) {
		return JSON.parse(JSON.stringify(toRaw(obj)));
	}

	function isDocDirty() {
		if (!isLoaded.value) return false;
		return (
			JSON.stringify(doc.value) !== JSON.stringify(originalDocSnapshot.value) ||
			JSON.stringify(conditions.value) !== JSON.stringify(originalConditions.value) ||
			JSON.stringify(actions.value) !== JSON.stringify(originalActions.value)
		);
	}

	function markDirty(force = false) {
		if (!isLoaded.value && !force) return;

		const isDirty = isDocDirty();
		if (isDirty !== dirty.value) {
			dirty.value = isDirty;
			const active = frappe?.ui?.form?.get_active?.();
			if (active) active.dirty = isDirty;
		}
	}

	function clearDirty() {
		dirty.value = false;
		const active = frappe?.ui?.form?.get_active?.();
		if (active) active.dirty = false;
	}

	// ========== CONDITION & ACTION OPERATIONS ==========
	function getConditionById(id) {
		return conditionsMap.value[id] || null;
	}

	function isConditionCollapsed(id) {
		return collapsed[id];
	}

	function toggleConditionCollapse(id) {
		collapsed[id] = !collapsed[id];
	}

	function setConditionCollapsed(id, value) {
		collapsed[id] = value;
	}

	function focusCondition(id) {
		focusedConditionId.value = id;
	}

	function markDirtyIfChanged(field, oldVal, newVal) {
		if (oldVal !== newVal) {
			markDirty();
		}
	}
	function get_new_child_template(doctype, parentfield) {
		let user = frappe.session.user;
		return {
			docstatus: 0,
			doctype: doctype,
			name: frappe.model.get_new_name(doctype),
			parent: doc.value.name,
			parentfield: parentfield,
			parenttype: doc.value.doctype,
			__islocal: 1,
			__unsaved: 1,
			owner: user,
			creation: "",
			modified_by: user,
			modified: "",
		};
	}
	function add_child(doctype, parentfield, defaults = {}, idx = null) {
		const child = get_new_child_template(doctype, parentfield);

		Object.assign(child, defaults);

		let targetList;
		if (parentfield === "conditions") {
			targetList = conditions.value;

			// Compute idx relative to the same parent_condition_id
			const parentId = child.parent_condition_id || "ROOT";
			const siblingCount = targetList.filter(
				(c) => (c.parent_condition_id || "ROOT") === parentId,
			).length;
			child.idx = idx != null ? idx : siblingCount + 1;
		} else if (parentfield === "actions") {
			targetList = actions.value;
			child.idx = idx != null ? idx : targetList.length + 1;
		} else {
			console.warn(`Unknown parentfield: ${parentfield}`);
			return;
		}

		targetList.push(child);
		markDirty();
		return child;
	}

	function addCondition(parentId = "ROOT") {
		const id = generateUniqueId();
		const defaults = serviceUIConfig.value?.["Rule Condition"]?.defaults || {};

		const newCond = add_child(
			"Rule Condition",
			"conditions",
			{
				condition_id: id,
				parent_condition_id: parentId,
				is_group: 0,
				left_value_source: "Document Field",
				operator: "==",
				...defaults,
			},
			//id,
		);

		//conditions.value.push(newCond);
		//markDirty();
		focusCondition(id);
		return newCond;
	}

	function addGroup(parentId = "ROOT") {
		const id = generateUniqueId();
		const newCond = add_child(
			"Rule Condition",
			"conditions",
			{
				condition_id: id,
				parent_condition_id: parentId,
				is_group: 1,
				group_operator: "AND",
			},
			//id,
		);
		//conditions.value.push(newCond);
		//markDirty();
		focusCondition(id);
		return newCond;
	}

	function removeCondition(id) {
		const allIds = collectRecursiveChildren(id);
		conditions.value = conditions.value.filter((c) => !allIds.includes(c.condition_id));
		markDirty();
	}

	function duplicateInLayout(original) {
		const raw = toRaw(original);
		let doctype = raw.doctype;
		let parentfield = raw.parentfield;
		const idMap = new Map();
		const toDup = collectRecursiveConditions(raw.condition_id);

		const clones = toDup.map((item) => {
			const newId = generateUniqueId();
			const child = get_new_child_template(doctype, parentfield); //must used to make the new duplicate items as new
			idMap.set(item.condition_id, newId);
			return {
				...deepClone(toRaw(item)),
				condition_id: newId,
				...child,
			};
		});

		for (const c of clones) {
			if (idMap.has(c.parent_condition_id)) {
				c.parent_condition_id = idMap.get(c.parent_condition_id);
			} else {
				c.parent_condition_id = raw.parent_condition_id;
			}
		}

		conditions.value.push(...clones);
		const root = clones.find((c) => c.condition_id === idMap.get(original.condition_id));
		if (root) focusCondition(root.condition_id);
		markDirty();
		return root;
	}

	function updateCondition(id) {
		markDirty();
	}

	function moveCondition(id, newParentId, insertIndex = null) {
		const node = getConditionById(id);
		if (!node) return;
		node.parent_condition_id = newParentId;

		const filtered = conditions.value.filter((c) => c.condition_id !== id);
		if (insertIndex == null) filtered.push(node);
		else filtered.splice(insertIndex, 0, node);

		conditions.value = filtered;
		markDirty();
	}

	function collectRecursiveConditions(id) {
		const all = [],
			queue = [id];
		while (queue.length) {
			const current = queue.pop();
			const node = getConditionById(current);
			if (!node) continue;
			all.push(node);
			queue.push(...childConditions(current).map((c) => c.condition_id));
		}
		return all;
	}

	function collectRecursiveChildren(id) {
		const all = [id],
			queue = [id];
		while (queue.length) {
			const current = queue.pop();
			for (const child of childConditions(current)) {
				all.push(child.condition_id);
				queue.push(child.condition_id);
			}
		}
		return all;
	}

	function collapseAll() {
		for (const c of conditions.value) collapsed[c.condition_id] = true;
	}
	function expandAll() {
		for (const c of conditions.value) collapsed[c.condition_id] = false;
	}

	function undo() {
		history.undo();
		markDirty();
	}
	function redo() {
		history.redo();
		markDirty();
	}

	function init(frmInstance, serviceType, documentTypes) {
		history.pause();
		isLoaded.value = false;

		frm.value = frmInstance;
		doc.value = deepClone(frm.value.doc);
		originalDocSnapshot.value = deepClone(frm.value.doc);

		conditions.value = deepClone(frm.value.doc.conditions || []);
		actions.value = deepClone(frm.value.doc.actions || []);

		originalConditions.value = deepClone(conditions.value);
		originalActions.value = deepClone(actions.value);

		if (!conditions.value.length) {
			conditions.value.push({
				condition_id: "Root",
				is_group: 1,
				group_operator: "AND",
			});
		}

		nextTick(() => {
			isLoaded.value = true;
			markDirty(true); // Force-check dirty after load
			history.resume();
		});
	}

	onKeyDown("z", (e) => {
		if (e.ctrlKey && !e.shiftKey && history.canUndo.value) {
			history.undo();
		}
		if (e.ctrlKey && e.shiftKey && history.canRedo.value) {
			history.redo();
		}
	});

	function save_rule() {
		const f = frm.value;
		if (!f) return;

		// Sync Pinia → cur_frm.doc
		syncToDoc();

		frappe.dom.freeze(__("Saving..."));
		f.save()
			.then(() => {
				clearDirty();
				frappe.show_alert({ message: __("Rule saved"), indicator: "green" });
			})
			.catch((err) => {
				console.error("Save failed:", err);
				frappe.msgprint({
					title: __("Save Failed"),
					message: err.message || err,
					indicator: "red",
				});
			})
			.finally(() => {
				frappe.dom.unfreeze();
			});
	}
	function update_conditions() {
		if (!dirty.value && !frm.value.is_new()) return;

		frappe.dom.freeze(__("Saving..."));

		try {
			const syncedConditions = [];

			for (const [i, cond] of toRaw(conditions.value).entries()) {
				const isNew = cint(cond.__islocal) === 1 || !cond.name;

				const cleaned = {
					...deepClone(cond),
					doctype: "Rule Condition",
					parent: frm.value.docname,
					parenttype: "Rule",
					parentfield: "conditions",
					idx: i + 1,
				};

				if (isNew) {
					// Let Frappe assign the name
					cleaned.__islocal = 1;
					cleaned.__unsaved = 1;
				} else {
					cleaned.name = cond.name;
					// Clear these flags so Frappe doesn't reassign
					delete cleaned.__islocal;
					delete cleaned.__unsaved;
				}

				syncedConditions.push(cleaned);
			}

			return syncedConditions;
		} catch (e) {
			console.error("Failed to prepare updated conditions", e);
			return __("Failed to prepare condition data");
		} finally {
			frappe.dom.unfreeze();
		}
	}

	function syncToDoc() {
		const f = frm.value;
		if (!f) return;

		const syncedConditions = [];

		for (const [i, cond] of toRaw(conditions.value).entries()) {
			const isNew = cond.__islocal || !cond.name;

			syncedConditions.push({
				...deepClone(cond),
				doctype: "Rule Condition",
				parent: f.docname,
				parenttype: "Rule",
				parentfield: "conditions",
				idx: i + 1,
				__unsaved: 1, // needed in some Frappe versions
				name: isNew ? undefined : cond.name,
			});
		}
		console.table(
			syncedConditions.map((c) => ({
				idx: c.idx,
				name: c.name,
				islocal: c.__islocal,
				condition_id: c.condition_id,
			})),
		);

		// Update the form doc's table
		f.set_value("conditions", syncedConditions);
	}

	return {
		frm,
		doc,
		conditions,
		actions,
		collapsed,
		focusedConditionId,
		dirty,

		init,
		clearDirty,
		save_rule,
		markDirty,

		getConditionById,
		addCondition,
		addGroup,
		removeCondition,
		duplicateInLayout,
		updateCondition,
		moveCondition,

		isConditionCollapsed,
		toggleConditionCollapse,
		setConditionCollapsed,
		focusCondition,
		collapseAll,
		expandAll,
		markDirtyIfChanged,

		rootConditions,
		childConditions,
		conditionsMap,
		serviceUIConfig,
		mergedConditionFields,

		undo,
		redo,
		canUndo: computed(() => history.canUndo.value),
		canRedo: computed(() => history.canRedo.value),
		layoutMode,
		syncToDoc,
		update_conditions,
	};
});
