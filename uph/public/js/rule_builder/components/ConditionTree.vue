<script setup>
import { ref, computed, onMounted, nextTick, watch } from "vue";
import ConditionTree from "./ConditionTree.vue";
import GridRenderer from "./GridRenderer.vue";
import draggable from "vuedraggable";
import { useRuleBuilderStore } from "../store";
import {
	safeFrappeUtils,
	getFinalFields,
	loadDoctypeFields,
	evaluate_depends_on_value,
} from "../utils";
import { Switch } from "@headlessui/vue";
import DynamicField from "./DynamicField.vue";

const props = defineProps({
	conditionId: { type: String, required: true },
	depth: { type: Number, default: 0 },
});

const store = useRuleBuilderStore();
const utils = safeFrappeUtils();
const wrapper = ref(null);
const draggedId = ref(null);
const isHovered = ref(false);

// reactive refs
const conditionRef = computed(() => store.getConditionById(props.conditionId));
const children = computed(() => store.childConditions(props.conditionId));
const isGroup = computed(() => conditionRef.value?.is_group === 1);
const isCollapsed = computed(() => store.isConditionCollapsed(props.conditionId));
const isFocused = computed(() => store.focusedConditionId === props.conditionId);
const conditionFields = ref([]);

// drag group rule (keeps previous behavior)
const dragGroup = computed(() => ({
	name: "conditions",
	pull: true,
	put: (to, from) => {
		const toDepth = props.depth;
		const fromWrapper = from.el.closest?.(".condition-wrapper");
		if (!fromWrapper) return true;
		const fromComponent = fromWrapper.__vue__ || fromWrapper.__vnode?.component?.proxy;
		const fromDepth = fromComponent?.depth ?? 0;
		return fromDepth <= toDepth;
	},
}));

const isAnd = ref(conditionRef.value?.group_operator === "AND");
const isRTL = ref(false);

// computed selection & indeterminate
const isSelected = computed(() => store.isConditionSelected(props.conditionId));
const isIndeterminate = computed(() => {
	if (!isGroup.value) return false;
	const ch = children.value || [];
	const selectedCount = ch.filter((c) => store.isConditionSelected(c.condition_id)).length;
	return selectedCount > 0 && selectedCount < ch.length;
});

// parent doc context used by evaluate_depends_on_value
const parentDoc = computed(() => conditionRef.value?.__parent || store.doc || {});

// load fields on mount (await async store method)
onMounted(async () => {
	isRTL.value = document.documentElement.dir === "rtl";
	conditionFields.value = await store.getFieldsForDoctype("Rule Condition");
});

// keep group operator in sync
watch(
	() => isAnd.value,
	(val) => {
		if (!conditionRef.value) return;
		const op = val ? "AND" : "OR";
		if (conditionRef.value.group_operator !== op) {
			conditionRef.value.group_operator = op;
			store.markDirty();
		}
	},
);

// helpers: compute summary fields using standard Frappe meta
function getSummaryFields(condition) {
	if (!condition || !conditionFields.value?.length) return [];

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

	// fields to always include (if present and not blacklisted)
	const alwaysInclude = ["left_field_chain", "operator"];

	// preserve order from conditionFields.value
	const filtered = conditionFields.value.filter((f) => {
		if (!f || !f.fieldname) return false;
		if (blacklist.has(f.fieldname)) return false;
		if (f.hidden === 1) return false; // respect hidden meta
		if (alwaysInclude.includes(f.fieldname)) return true;

		// evaluate visibility & required using standard meta keys
		const visible = f.depends_on
			? evaluate_depends_on_value(f.depends_on, condition, parentDoc.value)
			: true;

		const reqd = f.mandatory_depends_on
			? evaluate_depends_on_value(f.mandatory_depends_on, condition, parentDoc.value)
			: !!f.reqd;

		const value = condition[f.fieldname];

		// Generic rule: hide any field that is NOT in_list_view once it has a value
		if (value !== undefined && value !== null && value !== "" && f.in_list_view !== 1) {
			return false;
		}

		// Show if required & has a value OR explicitly marked for list view
		return (
			(visible && reqd && value !== undefined && value !== null && value !== "") ||
			(visible && f.in_list_view === 1)
		);
	});

	return filtered.slice(0, 6);
}

const summaryFields = computed(() => getSummaryFields(conditionRef.value));
const limitedSummaryFields = computed(() => summaryFields.value.slice(0, 4));

// UI helpers
function toggleSelection() {
	if (isGroup.value) store.setGroupSelected(props.conditionId, !isSelected.value);
	else store.setConditionSelected(props.conditionId, !isSelected.value);
}
function focusSelf() {
	store.focusCondition(props.conditionId);
}
function toggleCollapse() {
	store.toggleConditionCollapse(props.conditionId);
}
function addChildCondition() {
	const n = store.addCondition(props.conditionId);
	if (n) store.focusCondition(n.condition_id);
}
function addChildGroup() {
	const n = store.addGroup(props.conditionId);
	if (n) store.focusCondition(n.condition_id);
}
function duplicate() {
	const d = store.duplicateInLayout(conditionRef.value);
	if (d) store.focusCondition(d.condition_id);
}
function remove() {
	if (props.conditionId === "Root") {
		frappe.confirm(__("Removing the root group deletes all children. Proceed?"), () =>
			store.removeCondition(props.conditionId),
		);
	} else {
		store.removeCondition(props.conditionId);
	}
}

// drag handlers
function onDragStart() {
	draggedId.value = props.conditionId;
	wrapper.value?.classList.add("dragging");
}
function onDragEnd() {
	draggedId.value = null;
	wrapper.value?.classList.remove("dragging");
}
function onDragChange({ added, moved }) {
	if (moved) {
		// reorder inside same group
		store.reorderInGroup(props.conditionId, moved.oldIndex, moved.newIndex);
	} else if (added) {
		store.moveCondition(added.element.condition_id, props.conditionId, added.newIndex);
	}
}

// field change -> update store and mark dirty
function onFieldChange({ field, oldVal, newVal }) {
	if (JSON.stringify(oldVal) !== JSON.stringify(newVal)) {
		store.updateConditionField(props.conditionId, field.fieldname, newVal);
		store.markDirty();
	}
}
</script>
<template>
	<div
		class="condition-wrapper"
		:class="{
			'is-focused': isFocused,
			'is-group': isGroup,
			'is-collapsed': isCollapsed,
			'is-dragging': draggedId === conditionId,
		}"
		:style="{
			marginLeft: `${depth * 5}px`,
			borderLeft: depth > 0 ? '3px solid #e5e7eb' : 'none',
			paddingLeft: depth > 0 ? '3px' : '0',
		}"
		ref="wrapper"
		@mouseenter="isHovered = true"
		@mouseleave="isHovered = false"
	>
		<div class="compact-row" @click="focusSelf">
			<div class="selection-cell">
				<input
					type="checkbox"
					:checked="isSelected"
					:indeterminate.prop="isGroup && isIndeterminate"
					@change.stop="toggleSelection"
				/>
			</div>

			<div class="drag-cell">
				<span
					class="drag-handle"
					v-html="utils.icon('drag', 'xs')"
					@dblclick.stop="toggleCollapse"
				/>
			</div>

			<div class="operator-cell">
				<Switch v-if="isGroup" v-model="isAnd" as="template">
					<button class="group-switch" :class="{ 'is-and': isAnd, 'is-or': !isAnd }" @click.stop />
				</Switch>
				<button
					v-else
					class="toggle-button"
					@click.stop="toggleCollapse"
					:aria-expanded="!isCollapsed"
				>
					{{ isCollapsed ? "▶" : "▼" }}
				</button>
			</div>

			<div class="summary-cell">
				<div v-if="isGroup" class="group-summary">
					<span v-html="utils.icon('folder', 'sm')" />
					<span>If {{ isAnd ? "all" : "any" }} of:</span>
					<span v-if="!isCollapsed">({{ children.length }})</span>
				</div>

				<div v-else class="condition-summary">
					<span v-html="utils.icon('file', 'sm')" />
					<div class="summary-fields">
						<!-- render the computed summary fields only -->
						<DynamicField
							v-for="field in limitedSummaryFields"
							:key="field.fieldname"
							:df="field"
							:doc="conditionRef"
							mode="labelless"
							@field-change="onFieldChange"
						/>
					</div>
				</div>
			</div>

			<div class="actions-cell">
				<div class="action-buttons" v-show="isFocused || isHovered">
					<template v-if="isGroup">
						<button class="action-button add-condition" @click.stop="addChildCondition">+</button>
						<button class="action-button add-group" @click.stop="addChildGroup">⋁</button>
					</template>
					<button class="action-button duplicate" @click.stop="duplicate">⎘</button>
					<button class="action-button delete" @click.stop="remove">✕</button>
				</div>
			</div>
		</div>

		<transition name="expand">
			<div v-if="!isCollapsed" class="expanded-content">
				<template v-if="isGroup">
					<draggable
						:list="children"
						item-key="condition_id"
						:group="dragGroup"
						handle=".drag-handle"
						ghost-class="dragging-ghost"
						drag-class="dragging-active"
						:animation="150"
						@start="onDragStart"
						@end="onDragEnd"
						@change="onDragChange"
					>
						<template #item="{ element }">
							<ConditionTree :condition-id="element.condition_id" :depth="depth + 1" />
						</template>
						<template #footer v-if="children.length === 0">
							<div class="empty-group">
								<p>{{ __("Drop conditions here or click") }} +</p>
							</div>
						</template>
					</draggable>
				</template>

				<template v-else>
					<div class="condition-form">
						<GridRenderer
							:doc="conditionRef"
							:fields="conditionFields"
							@field-change="onFieldChange"
						/>
					</div>
				</template>
			</div>
		</transition>
	</div>
</template>

<style scoped>
/* BASE STYLES */
.condition-wrapper {
	--row-height: 36px;
	--icon-size: 14px;
	--border-radius: 4px;
	--transition-speed: 0.15s;
	--color-primary: #3b82f6;
	--color-danger: #ef4444;
	--color-success: #10b981;
	--color-warning: #f59e0b;
	--color-text: #334155;
	--color-text-light: #64748b;
	--color-bg-hover: #f8fafc;
	--color-border: #e2e8f0;
	--color-bg-active: #f1f5f9;
	--focus-ring: 0 0 0 2px #bfdbfe;

	position: relative;
	margin-bottom: 2px;
	outline: none;
}

/* COMPACT ROW LAYOUT */
.compact-row {
	display: grid;
	grid-template-columns: 24px 24px 60px minmax(120px, 1fr) auto;
	align-items: center;
	height: var(--row-height);
	padding: 0 8px;
	border: 1px solid var(--color-border);
	border-radius: var(--border-radius);
	background: white;
	transition: all var(--transition-speed) ease;
	cursor: pointer;
	font-size: 0.8125rem;
}

.condition-wrapper:hover .compact-row {
	background-color: var(--color-bg-hover);
}

.condition-wrapper.is-focused .compact-row {
	border-color: var(--color-primary);
	box-shadow: var(--focus-ring);
}

/* CELL STYLES */
.selection-cell,
.drag-cell {
	display: flex;
	justify-content: center;
	align-items: center;
}
.summary-fields {
	display: flex;
	flex-wrap: nowrap;
	gap: 8px; /* spacing between fields */
	align-items: center;
	overflow: visible; /* optional: prevent overflow */
	position: relative;
}

.drag-handle {
	opacity: 0.3;
	cursor: grab;
	transition: all var(--transition-speed) ease;
	padding: 4px;
	font-size: var(--icon-size);
	color: var(--color-text-light);
}

.condition-wrapper:hover .drag-handle,
.condition-wrapper.is-focused .drag-handle {
	opacity: 0.8;
	color: var(--color-text);
}

.operator-cell {
	display: flex;
	justify-content: flex-start;
}

.toggle-button {
	width: 30px;
	height: 20px;
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 3px;
	background: none;
	border: none;
	color: var(--color-text-light);
	cursor: pointer;
	transition: all var(--transition-speed) ease;
	font-size: var(--icon-size);
}

.toggle-button:hover {
	color: var(--color-primary);
	background-color: var(--color-bg-active);
}

.summary-cell {
	overflow: visible;
	padding: 0 4px;
}

.group-summary,
.condition-summary {
	display: flex;
	align-items: center;
	gap: 6px;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.group-icon,
.condition-icon {
	font-size: var(--icon-size);
	flex-shrink: 0;
}

.group-icon {
	color: var(--color-warning);
}

.condition-icon {
	color: var(--color-primary);
}

.child-count {
	color: var(--color-text-light);
	font-size: 0.75em;
}

.actions-cell {
	display: flex;
	justify-content: flex-end;
}

/* ACTION BUTTONS */
.action-buttons {
	display: flex;
	gap: 4px;
	padding: 2px;
}

.action-button {
	width: 24px;
	height: 24px;
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 4px;
	border: 1px solid transparent;
	background: none;
	cursor: pointer;
	transition: all var(--transition-speed) ease;
	font-size: var(--icon-size);
	color: var(--color-text-light);
}

.action-button:hover {
	background-color: var(--color-bg-active);
	border-color: var(--color-border);
	color: var(--color-text);
}

.action-button.add-condition {
	color: var(--color-success);
}
.action-button.add-condition:hover {
	background-color: rgba(16, 185, 129, 0.1);
}

.action-button.add-group {
	color: var(--color-warning);
}
.action-button.add-group:hover {
	background-color: rgba(245, 158, 11, 0.1);
}

.action-button.duplicate {
	color: var(--color-primary);
}
.action-button.duplicate:hover {
	background-color: rgba(59, 130, 246, 0.1);
}

.action-button.delete {
	color: var(--color-danger);
}
.action-button.delete:hover {
	background-color: rgba(239, 68, 68, 0.1);
}

/* GROUP SWITCH TOGGLE */
.group-switch {
	--switch-width: 60px;
	--switch-height: 24px;
	--thumb-size: 18px;
	--thumb-offset: 2px;

	position: relative;
	width: var(--switch-width);
	height: var(--switch-height);
	display: inline-block;
	border: none;
	background: transparent;
	padding: 0;
	cursor: pointer;
}

.switch-track {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	border-radius: 12px;
	background-color: var(--color-bg-active);
	border: 1px solid var(--color-border);
	transition: all var(--transition-speed) ease;
}

.switch-thumb {
	position: absolute;
	top: var(--thumb-offset);
	left: var(--thumb-offset);
	width: var(--thumb-size);
	height: var(--thumb-size);
	border-radius: 50%;
	background-color: white;
	box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
	transition: transform var(--transition-speed) ease;
	z-index: 2;
}

.switch-labels {
	position: relative;
	display: flex;
	height: 100%;
	z-index: 1;
}

.label-and,
.label-or {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 0.6875rem;
	font-weight: 600;
	text-transform: uppercase;
	color: var(--color-text-light);
	transition: color var(--transition-speed) ease;
}

/* AND State */
.is-and .switch-track {
	background-color: rgba(16, 185, 129, 0.1);
	border-color: rgba(16, 185, 129, 0.3);
}

.is-and .switch-thumb {
	transform: translateX(calc(var(--switch-width) - var(--thumb-size) - (var(--thumb-offset) * 2)));
	background-color: var(--color-success);
}

.is-and .label-and {
	color: var(--color-success);
	font-weight: 700;
}

/* OR State */
.is-or .switch-track {
	background-color: rgba(245, 158, 11, 0.1);
	border-color: rgba(245, 158, 11, 0.3);
}

.is-or .switch-thumb {
	transform: translateX(var(--thumb-offset));
	background-color: var(--color-warning);
}

.is-or .label-or {
	color: var(--color-warning);
	font-weight: 700;
}

.group-switch:focus-visible {
	outline: 2px solid var(--color-primary);
	outline-offset: 2px;
	border-radius: 14px;
}

/* EXPANDED CONTENT */
.expand-enter-active,
.expand-leave-active {
	transition: all var(--transition-speed) ease;
	overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
	opacity: 0;
	transform: translateY(-5px);
	max-height: 0;
}

.group-children {
	padding: 2px 0 0 1px;
	border-left: 1px dashed var(--color-border);
	margin-left: 3px;
}

.empty-group {
	padding: 8px 12px;
	text-align: center;
	font-size: 0.75rem;
	color: var(--color-text-light);
	font-style: italic;
	border: 1px dashed var(--color-border);
	border-radius: var(--border-radius);
	margin-top: 4px;
}

.condition-form {
	padding: 8px;
	margin-top: 0px;
	border: 1px solid var(--color-border);
	border-radius: var(--border-radius);
	background: var(--color-bg-hover);
}

/* DRAG STATES */
.dragging-ghost .compact-row {
	background-color: #ebf8ff;
	border-color: #bee3f8;
}

.dragging-active {
	opacity: 0.6;
}

/* CHECKBOX */
input[type="checkbox"] {
	width: 14px;
	height: 14px;
	cursor: pointer;
	accent-color: var(--color-primary);
}
/* Add these to your parent component's styles */
.condition-wrapper {
	overflow: visible !important;
	contain: none !important;
}

.compact-row {
	overflow: visible !important;
}

.summary-cell {
	overflow: visible !important;
	contain: none !important;
	z-index: auto;
}

.summary-fields {
	overflow: visible !important;
	contain: none !important;
}

.expanded-content {
	overflow: visible !important;
	contain: none !important;
}

.grid-row,
.grid-cell {
	overflow: visible !important;
	contain: none !important;
}
/* ACCESSIBILITY */
.sr-only {
	position: absolute;
	width: 1px;
	height: 1px;
	padding: 0;
	margin: -1px;
	overflow: hidden;
	clip: rect(0, 0, 0, 0);
	white-space: nowrap;
	border-width: 0;
}
.grid-row,
.grid-cell {
	overflow: visible !important;
	contain: none !important;
}

/* Ensure the expanded content doesn't clip dropdowns */
.expanded-content {
	overflow: visible !important;
	contain: none !important;
}
/* FOCUS STATES */
.action-button:focus-visible,
.toggle-button:focus-visible,
.drag-handle:focus-visible,
.group-switch:focus-visible {
	outline: 2px solid var(--color-primary);
	outline-offset: 1px;
}
</style>
