<script setup>
import { ref, computed, onMounted, watch, nextTick } from "vue";
import ConditionTree from "./ConditionTree.vue";
import GridRenderer from "./GridRenderer.vue";
import draggable from "vuedraggable";
import { useRuleBuilderStore } from "../store";
import { getServiceUIConfig, safeFrappeUtils } from "../utils";
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
const isRTL = ref(false);
const isSelected = ref(false);
const isIndeterminate = ref(false);
const summaryFields = computed(() => {
	if (!conditionFields.value.length) return [];

	// Find left_field_path field
	const leftField = conditionFields.value.find((f) => f.fieldname === "left_field_path");
	// Find operator field
	const operatorField = conditionFields.value.find((f) => f.fieldname === "operator");
	// Find all required fields (mandatory)
	const requiredFields = conditionFields.value.filter((f) => f.reqd);

	// Combine: left_field_path, operator, then required fields that are not duplicates
	const fields = [];

	if (leftField) fields.push(leftField);
	if (operatorField) fields.push(operatorField);

	requiredFields.forEach((f) => {
		if (f.fieldname !== "left_field_path" && f.fieldname !== "operator") {
			fields.push(f);
		}
	});

	// Optionally limit to first 4 total fields
	return fields.slice(0, 4);
});

// Initialize RTL on mount
onMounted(() => {
	isRTL.value = document.documentElement.dir === "rtl";
});

// Add selection handling
function toggleSelection() {
	if (isGroup.value) {
		store.setGroupSelected(props.conditionId, !isSelected.value);
	} else {
		store.setConditionSelected(props.conditionId, !isSelected.value);
	}
}

// Update selection state when store changes
watch(
	() => store.selectedConditions,
	() => {
		isSelected.value = store.isConditionSelected(props.conditionId);

		// Handle indeterminate state for groups
		if (isGroup.value) {
			const children = store.childConditions(props.conditionId);
			const selectedChildren = children.filter((child) =>
				store.isConditionSelected(child.condition_id),
			).length;

			isIndeterminate.value = selectedChildren > 0 && selectedChildren < children.length;
		}
	},
	{ deep: true },
);

// Update indent style for RTL/LTR
const indentStyle = computed(() => {
	if (isRTL.value) {
		return {
			marginRight: `${props.depth * 5}px`,
			borderRight: props.depth > 0 ? "3px solid #e5e7eb" : "none",
			paddingRight: props.depth > 0 ? "3px" : "0",
		};
	} else {
		return {
			marginLeft: `${props.depth * 5}px`,
			borderLeft: props.depth > 0 ? "3px solid #e5e7eb" : "none",
			paddingLeft: props.depth > 0 ? "3px" : "0",
		};
	}
});

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
		class="condition-wrapper"
		:class="{
			'is-focused': isFocused,
			'is-group': isGroup,
			'is-collapsed': isCollapsed,
			'is-dragging': draggedId === conditionId,
		}"
		:style="indentStyle"
		ref="wrapper"
		@mouseenter="isHovered = true"
		@mouseleave="isHovered = false"
	>
		<!-- COMPACT ROW LAYOUT -->
		<div class="compact-row" @click="focusSelf">
			<!-- Selection Checkbox -->
			<div class="selection-cell">
				<input
					type="checkbox"
					:checked="isSelected"
					:indeterminate.prop="isGroup && isIndeterminate"
					@change="toggleSelection"
					@click.stop
				/>
			</div>

			<!-- Drag Handle -->
			<div class="drag-cell">
				<span
					class="drag-handle"
					v-html="utils.icon('drag', 'xs')"
					@click.stop
					@dblclick.stop="toggleCollapse"
				/>
			</div>

			<!-- Operator/Toggle -->
			<div class="operator-cell">
				<Switch v-if="isGroup" v-model="isAnd" as="template">
					<button class="group-switch" :class="{ 'is-and': isAnd, 'is-or': !isAnd }" @click.stop>
						<span class="sr-only">Toggle between AND and OR</span>
						<span class="switch-track">
							<span class="switch-thumb" />
						</span>
						<span class="switch-labels">
							<span class="label-and">AND</span>
							<span class="label-or">OR</span>
						</span>
					</button>
				</Switch>

				<button
					v-if="!isGroup"
					class="toggle-button"
					@click.stop="toggleCollapse"
					:aria-expanded="!isCollapsed"
				>
					<span aria-hidden="true">{{ isCollapsed ? "▶" : "▼" }}</span>
				</button>
			</div>

			<!-- Summary Content -->
			<div class="summary-cell">
				<div v-if="isGroup" class="group-summary">
					<span class="group-icon" v-html="utils.icon('folder', 'sm')" />
					<span class="group-label">If {{ isAnd ? "all" : "any" }} of:</span>
					<span class="child-count" v-if="!isCollapsed">({{ children.length }})</span>
				</div>
				<div v-else class="condition-summary">
					<span class="condition-icon" v-html="utils.icon('file', 'sm')" />
					<div class="summary-fields">
						<DynamicField
							v-for="field in summaryFields"
							:key="field.fieldname"
							:df="field"
							:doc="condition"
							mode="labelless"
							@field-change="onFieldChange"
							:readonly="true"
						/>
					</div>
				</div>
			</div>

			<!-- Action Buttons -->
			<div class="actions-cell">
				<div class="action-buttons" v-show="isFocused || isHovered">
					<template v-if="isGroup">
						<button
							class="action-button add-condition"
							@click.stop="addChildCondition"
							aria-label="Add child condition"
						>
							<span aria-hidden="true">+</span>
						</button>
						<button
							class="action-button add-group"
							@click.stop="addChildGroup"
							aria-label="Add child group"
						>
							<span aria-hidden="true">⋁</span>
						</button>
					</template>
					<button class="action-button duplicate" @click.stop="duplicate" aria-label="Duplicate">
						<span aria-hidden="true">⎘</span>
					</button>
					<button class="action-button delete" @click.stop="remove" aria-label="Delete">
						<span aria-hidden="true">✕</span>
					</button>
				</div>
			</div>
		</div>

		<!-- EXPANDED CONTENT -->
		<transition name="expand">
			<div v-if="!isCollapsed" class="expanded-content">
				<template v-if="isGroup">
					<div class="group-children">
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
					</div>
				</template>
				<template v-else>
					<div class="condition-form">
						<GridRenderer
							:doc="condition"
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
	overflow: hidden; /* optional: prevent overflow */
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
	overflow: hidden;
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

/* FOCUS STATES */
.action-button:focus-visible,
.toggle-button:focus-visible,
.drag-handle:focus-visible,
.group-switch:focus-visible {
	outline: 2px solid var(--color-primary);
	outline-offset: 1px;
}
</style>
