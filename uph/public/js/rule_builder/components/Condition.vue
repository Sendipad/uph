<script setup>
import { ref, computed, onMounted, watch, nextTick } from "vue";
import Condition from "./Condition.vue";
import GridRenderer from "./GridRenderer.vue";
import draggable from "vuedraggable";
import { useRuleBuilderStore } from "../store";
import { getServiceUIConfig, safeFrappeUtils } from "../utils";
import { Switch } from "@headlessui/vue";

const props = defineProps({
	conditionId: { type: String, required: true },
	depth: { type: Number, default: 0 },
});

const store = useRuleBuilderStore();
const utils = safeFrappeUtils();
const wrapper = ref(null);
const draggedId = ref(null);
const isHovered = ref(false);

const condition = computed(() => store.getConditionById(props.conditionId));
const children = computed(() => store.childConditions(props.conditionId));
const isGroup = computed(() => condition.value?.is_group === 1);
const isCollapsed = computed(() => store.isConditionCollapsed(props.conditionId));
const isFocused = computed(() => store.focusedConditionId === props.conditionId);
const conditionFields = ref([]);
const dragGroup = computed(() => ({
	name: "conditions",
	pull: true,
	put: (to, from, draggedEl) => {
		const toDepth = props.depth;
		const fromWrapper = from.el.closest(".condition-wrapper");

		if (!fromWrapper) return true;

		const fromComponent = fromWrapper.__vue__ || fromWrapper.__vnode?.component?.proxy;
		const fromDepth = fromComponent?.depth ?? 0;

		return fromDepth <= toDepth;
	},
}));
const isAnd = ref(condition.value?.group_operator === "AND");

const indentStyle = computed(() => ({
	marginLeft: `${props.depth * 20}px`,
	borderLeft: props.depth > 0 ? "3px solid #e5e7eb" : "none",
	paddingLeft: props.depth > 0 ? "12px" : "0",
}));

const summaryText = computed(() => {
	if (!condition.value) return "⚠️ Invalid condition";
	const c = condition.value;

	// Build a meaningful summary
	const leftValue = c.left_field_path || c.left_value_literal || c.left_value_context_key || "...";

	const operator = c.operator || "?";

	const rightValue =
		c.right_field_path || c.right_value_literal || c.right_value_context_key || "...";

	return `${leftValue} ${operator} ${rightValue}`;
});

const groupSummary = computed(
	() => `${condition.value?.name || __("Condition Group")} (${children.value.length})`,
);

onMounted(async () => {
	await loadConditionFields();
});
// Sync changes back to condition and mark dirty:
watch(isAnd, (newVal, oldVal) => {
	if (!condition.value) return;
	const newOperator = newVal ? "AND" : "OR";

	if (condition.value.group_operator !== newOperator) {
		condition.value.group_operator = newOperator;
		store.markDirty();
	}
});
watch(
	() => store.doc.rule_service_type,
	async () => {
		await loadConditionFields();
	},
);
function onFieldChange({ field, oldVal, newVal }) {
	if (JSON.stringify(oldVal) !== JSON.stringify(newVal)) {
		store.markDirty();
	}
}

async function loadConditionFields() {
	try {
		const fields = frappe.meta.get_docfields("Rule Condition");
		if (Array.isArray(fields)) {
			const blacklist = new Set([
				"group_a_column",
				"group_b_column",
				"group_logic_section",
				"is_group",
				"indent",
				"group_operator",
				"logical_operator",
				"condition_section",
			]);

			conditionFields.value = fields.filter((f) => {
				// Exclude by fieldname
				if (blacklist.has(f.fieldname)) return false;

				// Exclude fields meant for groups only via depends_on
				const depends = f.depends_on || "";
				const isGroupOnly = /doc\.is_group\s*={1,3}\s*1/.test(depends);
				return !isGroupOnly;
			});
		} else {
			console.warn("get_docfield did not return an array");
			conditionFields.value = [];
		}
	} catch (e) {
		console.error("Failed to load condition fields from meta:", e);
		conditionFields.value = [];
	}
}

function onDragEnter() {
	wrapper.value?.classList.add("drag-over-highlight");
}
function onDragLeave() {
	wrapper.value?.classList.remove("drag-over-highlight");
}

function onDragStart(event) {
	if (event.dataTransfer) {
		event.dataTransfer.setData("condition_id", props.conditionId);
		event.dataTransfer.effectAllowed = "move";
	}

	draggedId.value = props.conditionId;

	if (wrapper.value) {
		wrapper.value.classList.add("dragging");
	}
}
function onReorder(evt) {
	const { added, moved } = evt;
	if (moved) {
		store.reorderInGroup(props.conditionId, moved.oldIndex, moved.newIndex);
	} else if (added) {
		const id = added.element.condition_id;
		store.moveCondition(id, props.conditionId, added.newIndex);
	}
}

function onDragEnd(event) {
	draggedId.value = null;
	if (wrapper.value) {
		wrapper.value.classList.remove("dragging");
	}
}

function handleDrop(event) {
	event.preventDefault();
	const droppedId = event.dataTransfer?.getData("condition_id");
	if (!droppedId || droppedId === props.conditionId) return;

	// Drop into current group
	const groupId = props.conditionId;
	const isGroupTarget = isGroup.value;

	const newParentId = isGroupTarget ? props.conditionId : condition.value.parent_condition_id;
	store.moveCondition(droppedId, newParentId);
}

function focusSelf() {
	store.focusCondition(props.conditionId);
}

function toggleCollapse() {
	store.toggleConditionCollapse(props.conditionId);
}

function update() {
	const old = { ...condition.value };
	nextTick(() => {
		if (
			condition.value?.group_operator !== old.group_operator // or other relevant fields
		) {
			store.markDirty();
		}
	});
}

function addChildCondition() {
	const newCondition = store.addCondition(props.conditionId);
	if (newCondition) {
		store.focusCondition(newCondition.condition_id);
	}
}
function onDragChange(evt) {
	const { added, moved } = evt;
	if (moved) {
		// Internal reorder
		const { oldIndex, newIndex } = moved;
		if (oldIndex === newIndex) return;

		const siblings = store.childConditions(props.conditionId);
		const movedId = siblings[oldIndex]?.condition_id;
		if (!movedId) return;

		store.moveCondition(movedId, props.conditionId, newIndex);
	} else if (added) {
		// Cross-group drop
		const { newIndex, element } = added;
		if (!element?.condition_id) return;
		store.moveCondition(element.condition_id, props.conditionId, newIndex);
	}
}

function addChildGroup() {
	const newGroup = store.addGroup(props.conditionId);
	if (newGroup) {
		store.focusCondition(newGroup.condition_id);
	}
}
function onMove({ draggedContext, to }) {
	const targetGroupId = to.el.closest(".condition-wrapper")?.__vue__?.conditionId;
	// Allow dropping only into actual groups:
	return store.getConditionById(targetGroupId)?.is_group === 1;
}

function duplicate() {
	const duplicated = store.duplicateInLayout(condition.value);
	if (duplicated) {
		store.focusCondition(duplicated.condition_id);
	}
}
function remove() {
	if (props.conditionId === "Root") {
		frappe.confirm(
			__(
				"You are about to remove the root group. This will delete all its child conditions. Are you sure?",
			),
			() => {
				store.removeCondition(props.conditionId);
			},
		);
	} else {
		store.removeCondition(props.conditionId);
	}
}
</script>

<template>
	<div
		class="condition-group-wrapper with-connector"
		:class="{ focused: isFocused, group: isGroup, collapsed: isCollapsed }"
		:style="indentStyle"
		ref="wrapper"
		@click="focusSelf"
		@mouseenter="isHovered = true"
		@mouseleave="isHovered = false"
	>
		<!-- Group Header -->
		<template v-if="isGroup">
			<div class="group-header">
				<span class="drag-handle" v-html="utils.icon('drag', 'xs')" />

				<Switch
					v-model="isAnd"
					as="button"
					:class="['group-operator-switch', isAnd ? 'bg-green-600' : 'bg-yellow-600']"
				>
					{{ isAnd ? "AND" : "OR" }}
				</Switch>
				<div class="group-actions" v-show="isFocused || isHovered">
					<button @click="addChildCondition">+</button>
					<button @click="addChildGroup">⋁</button>
					<button @click="duplicate">⎘</button>
					<button @click="remove" class="danger">✕</button>
					<button @click="toggleCollapse">{{ isCollapsed ? "▶" : "▼" }}</button>
				</div>
			</div>

			<div v-if="isCollapsed" class="group-summary">{{ groupSummary }}</div>

			<div v-else class="group-children">
				<draggable
					:list="children"
					item-key="condition_id"
					:group="dragGroup"
					handle=".drag-handle"
					ghost-class="dragging-ghost"
					:animation="200"
					@start="onDragStart"
					@end="onDragEnd"
					@change="onDragChange"
				>
					<template #item="{ element }">
						<Condition :condition-id="element.condition_id" :depth="depth + 1" />
					</template>
				</draggable>
			</div>
		</template>

		<!-- Atomic Condition -->
		<template v-else>
			<div class="condition-header vertical-layout">
				<!-- Left: drag + vertical buttons -->
				<div class="left-toolbar">
					<span class="drag-handle" v-html="utils.icon('drag', 'xs')" />
					<div class="condition-actions" v-show="isFocused || isHovered">
						<button @click="toggleCollapse">{{ isCollapsed ? "▶" : "▼" }}</button>

						<button @click="duplicate">⎘</button>
						<button @click="remove" class="danger">✕</button>
					</div>
				</div>

				<!-- Right: form -->
				<div class="condition-content" v-if="!isCollapsed">
					<GridRenderer :doc="condition" :fields="conditionFields" @field-change="onFieldChange" />
				</div>
			</div>

			<div v-if="isCollapsed" class="condition-summary">
				<span v-html="utils.icon('file', 'sm')" />
				{{ summaryText }}
			</div>
		</template>
	</div>
</template>

<style scoped>
.btn {
	padding: 10px 16px;
	border-radius: 8px;
	font-weight: 500;
	font-size: 14px;
	cursor: pointer;
	transition: all 0.2s ease;
	border: none;
	display: flex;
	align-items: center;
	gap: 6px;
}

.btn-primary {
	background: #3b82f6;
	color: white;
}

.btn-primary:hover {
	background: #2563eb;
}

.btn-outline {
	background: transparent;
	border: 1px solid #cbd5e1;
	color: #334155;
}

.btn-outline:hover {
	background: #f1f5f9;
	border-color: #94a3b8;
}

/* Condition styles */
.condition-group-wrapper {
	border: 1px solid #e2e8f0;
	border-radius: 12px;
	background: white;
	margin-bottom: 16px;
	padding: 18px;
	transition: all 0.25s ease;
	position: relative;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}

.condition-group-wrapper.group {
	background-color: #f8fbff;
	border-color: #d1e0ff;
}

.condition-group-wrapper.focused {
	border-color: #3b82f6;
	box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.condition-group-wrapper.collapsed {
	padding: 14px 18px;
}

.with-connector::before {
	content: "";
	position: absolute;
	top: 28px;
	left: -16px;
	height: calc(100% - 28px);
	width: 16px;
	border-top: 2px solid #cbd5e1;
	border-left: 2px solid #cbd5e1;
	border-top-left-radius: 8px;
}

/* Group Header */
.group-header {
	display: flex;
	align-items: center;
	gap: 14px;
	padding-bottom: 16px;
	position: relative;
}

/* Drag handle */
.drag-handle {
	cursor: grab;
	color: #94a3b8;
	opacity: 0.7;
	transition: all 0.2s;
	display: flex;
	align-items: center;
	justify-content: center;
	width: 30px;
	height: 30px;
	border-radius: 8px;
	background: #f1f5f9;
}

.drag-handle svg {
	width: 16px;
	height: 16px;
}

.drag-handle:hover {
	opacity: 1;
	background: #e2e8f0;
	color: #64748b;
}

/* Group operator switch */
.group-operator-switch {
	width: 70px;
	height: 32px;
	border-radius: 50px;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	color: white;
	font-size: 12px;
	font-weight: 600;
	cursor: pointer;
	transition: all 0.2s ease;
	border: none;
	outline: none;
	box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
	letter-spacing: 0.5px;
	text-transform: uppercase;
}

.group-operator-switch.bg-green-600 {
	background-color: #10b981;
}

.group-operator-switch.bg-green-600:hover {
	background-color: #059669;
}

.group-operator-switch.bg-yellow-600 {
	background-color: #f59e0b;
}

.group-operator-switch.bg-yellow-600:hover {
	background-color: #d97706;
}

/* Group actions */
.group-actions {
	display: flex;
	gap: 8px;
	margin-left: auto;
}

.group-actions button {
	background: #f1f5f9;
	border: none;
	width: 34px;
	height: 34px;
	border-radius: 8px;
	cursor: pointer;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #64748b;
	font-size: 16px;
	transition: all 0.2s;
}

.group-actions button:hover {
	background-color: #e2e8f0;
	color: #475569;
}

.group-actions button.danger {
	color: #ef4444;
}

.group-actions button.danger:hover {
	background-color: #fee2e2;
	color: #dc2626;
}

/* Children list inside group */
.group-children {
	position: relative;
	margin-left: 36px;
	padding-left: 18px;
}

.group-children::before {
	content: "";
	position: absolute;
	top: -18px;
	bottom: 16px;
	left: 0;
	width: 2px;
	background-color: #cbd5e1;
}

/* Condition Header */
.condition-header {
	display: flex;
	gap: 16px;
	align-items: flex-start;
}

.left-toolbar {
	display: flex;
	flex-direction: column;
	gap: 10px;
	padding-top: 6px;
}

/* Condition actions */
.condition-actions {
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.condition-actions button {
	width: 34px;
	height: 34px;
	background: #f1f5f9;
	border: none;
	border-radius: 8px;
	cursor: pointer;
	color: #64748b;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 16px;
	transition: all 0.2s;
}

.condition-actions button:hover {
	background-color: #e2e8f0;
	color: #475569;
}

.condition-actions button.danger {
	color: #ef4444;
}

.condition-actions button.danger:hover {
	background-color: #fee2e2;
	color: #dc2626;
}

/* Condition form */
.condition-content {
	flex-grow: 1;
	padding: 4px 0;
}

.condition-form {
	display: grid;
	grid-template-columns: 1.2fr 1fr 1.5fr;
	gap: 14px;
	align-items: center;
}

.condition-form select,
.condition-form input {
	padding: 10px 14px;
	border: 1px solid #cbd5e1;
	border-radius: 8px;
	background: white;
	font-size: 14px;
	color: #334155;
	transition: all 0.2s;
	height: 40px;
}

.condition-form select:focus,
.condition-form input:focus {
	outline: none;
	border-color: #93c5fd;
	box-shadow: 0 0 0 3px rgba(147, 197, 253, 0.3);
}

/* Condition summary */
.condition-summary {
	padding: 14px 18px;
	background: #f8fafc;
	border-radius: 8px;
	margin-top: 14px;
	display: flex;
	align-items: center;
	gap: 10px;
	font-size: 14px;
	color: #475569;
	border: 1px dashed #cbd5e1;
}

.condition-summary svg {
	color: #94a3b8;
	flex-shrink: 0;
}

/* Group summary */
.group-summary {
	padding: 14px 18px;
	background: #f8fafc;
	border-radius: 8px;
	margin-top: 14px;
	display: flex;
	align-items: center;
	gap: 10px;
	font-size: 14px;
	color: #475569;
	border: 1px dashed #cbd5e1;
}

.group-summary svg {
	color: #94a3b8;
	flex-shrink: 0;
}

/* Collapsed state */
.condition-group-wrapper.collapsed .condition-content {
	display: none;
}

/* RTL support */
html[dir="rtl"] .with-connector::before {
	left: auto;
	right: -16px;
	border-left: none;
	border-right: 2px solid #cbd5e1;
	border-top-left-radius: 0;
	border-top-right-radius: 8px;
}

html[dir="rtl"] .group-children {
	margin-left: 0;
	margin-right: 36px;
	padding-left: 0;
	padding-right: 18px;
}

html[dir="rtl"] .group-children::before {
	left: auto;
	right: 0;
}

/* Footer */
.footer {
	text-align: center;
	color: #64748b;
	font-size: 14px;
	padding: 20px 0;
	border-top: 1px solid #e2e8f0;
	margin-top: 20px;
}

/* Dragging state */
.dragging-ghost {
	opacity: 0.7;
	transform: scale(0.98);
	box-shadow: 0 6px 15px rgba(0, 0, 0, 0.1);
}

.drag-over-highlight {
	border-color: #3b82f6 !important;
	background-color: #e0f2fe;
}
</style>
