<template>
	<div
		class="condition-wrapper"
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
				<select v-model="condition.group_operator" @change="update" class="group-operator">
					<option value="AND">AND</option>
					<option value="OR">OR</option>
				</select>
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
					<GridRenderer :doc="condition" :fields="conditionFields" />
				</div>
			</div>

			<div v-if="isCollapsed" class="condition-summary">
				<span v-html="utils.icon('file', 'sm')" />
				{{ summaryText }}
			</div>
		</template>
	</div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from "vue";
import Condition from "./Condition.vue";
import GridRenderer from "./GridRenderer.vue";
import draggable from "vuedraggable";
import { useRuleBuilderStore } from "../store";
import { getServiceUIConfig, safeFrappeUtils } from "../utils";

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

watch(
	() => store.doc.rule_service_type,
	async () => {
		await loadConditionFields();
	},
);
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
	store.removeCondition(props.conditionId);
}
</script>

<style scoped>
.condition-wrapper {
	border: 1px solid #e5e7eb;
	border-radius: 8px;
	background: white;
	margin-bottom: 12px;
	padding: 12px;
	transition: all 0.2s ease;
	position: relative;
}

.condition-wrapper.group {
	background-color: #f8fbff;
	border-color: #dbeafe;
}

.condition-wrapper.focused {
	border-color: #3b82f6;
	box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.condition-wrapper.collapsed {
	padding: 8px 12px;
}

.condition-wrapper.dragging {
	opacity: 0.6;
	transform: scale(0.98);
}

.condition-error {
	padding: 12px;
	background-color: #fef2f2;
	color: #b91c1c;
	border-radius: 6px;
	display: flex;
	align-items: center;
	gap: 8px;
}

/* 🟦 Drag handle icon */
.drag-handle {
	cursor: grab;
	color: #6b7280;
	opacity: 0.6;
	transition: opacity 0.2s;
}
.condition-wrapper:hover .drag-handle,
.condition-wrapper.focused .drag-handle {
	opacity: 1;
}

/* 🧱 GROUP layout */
.group-header {
	display: flex;
	align-items: center;
	gap: 8px;
}
.group-operator {
	padding: 4px 8px;
	border-radius: 4px;
	border: 1px solid #d1d5db;
	background: white;
	font-size: 0.9rem;
}

/* 🔹 GROUP actions: INLINE */
.group-actions {
	display: flex;
	gap: 6px;
	margin-left: auto;
}
.group-actions button {
	background: none;
	border: none;
	padding: 4px 6px;
	border-radius: 4px;
	cursor: pointer;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #374151;
}
.group-actions button:hover {
	background-color: #f3f4f6;
}
.group-actions button.danger:hover {
	background-color: #fee2e2;
	color: #b91c1c;
}

/* 🟩 ATOMIC condition layout */
.condition-header {
	display: flex;
	align-items: flex-start;
	gap: 12px;
}
.vertical-layout {
	display: flex;
	align-items: flex-start;
	gap: 12px;
}

/* Left toolbar for condition buttons + handle */
.left-toolbar {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 6px;
	margin-right: 8px;
	min-width: 36px; /* 👈 Prevent shrinking */
}

/* Right content: grid form */
.condition-content {
	flex-grow: 1;
}

/* 🔸 CONDITION actions: VERTICAL */
.condition-actions {
	display: flex;
	flex-direction: column;
	gap: 6px;
}
.condition-actions button {
	width: 28px;
	height: 28px;
	padding: 4px;
	background: none;
	border: none;
	border-radius: 4px;
	cursor: pointer;
	color: #374151;
	display: flex;
	align-items: center;
	justify-content: center;
}
.condition-actions button:hover {
	background-color: #f3f4f6;
}
.condition-actions button.danger:hover {
	background-color: #fee2e2;
	color: #b91c1c;
}

/* 📄 Summary (group or atomic) */
.group-summary,
.condition-summary {
	padding: 8px 12px;
	background: #f9fafb;
	border-radius: 6px;
	margin-top: 8px;
	display: flex;
	align-items: center;
	gap: 8px;
	font-size: 0.9rem;
}

/* Drop zone */
.collapsed-drop-zone {
	border: 2px dashed #cbd5e1;
	border-radius: 6px;
	padding: 16px;
	text-align: center;
	margin-top: 8px;
	background: #f8fafc;
	color: #64748b;
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 8px;
	cursor: pointer;
	transition: all 0.2s;
}
.collapsed-drop-zone:hover {
	border-color: #94a3b8;
	background: #f1f5f9;
}

/* Children list inside group */
.group-children {
	margin-top: 12px;
	display: flex;
	flex-direction: column;
	gap: 12px;
}

/* While dragging */
.dragging-ghost {
	opacity: 0.7;
	transform: scale(0.98);
	box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}
.drag-over-highlight {
	border-color: #3b82f6 !important;
	background-color: #e0f2fe;
}
</style>
