//file : apps/uph/uph/public/js/rule_builder/RuleBuilder.vue
<template>
	<div class="rule-builder">
		<!-- Header -->
		<!-- Add a toggle button or detect scroll -->

		<!-- Builder -->
		<div class="builder-container" :class="{ 'actions-visible': showActionsPanel }">
			<!-- Conditions Section -->

			<section class="conditions">
				<div class="section-header">
					<h3>{{ __("Conditions") }}</h3>
					<div class="group-actions">
						<button @click="store.collapseAll">{{ __("Collapse All") }}</button>
						<button @click="store.expandAll">{{ __("Expand All") }}</button>
						<button @click="store.addGroup" class="btn btn-add">
							<span v-html="utils.icon('plus', 'xs')"></span>
							{{ __("Add Group") }}
						</button>
						<button @click="store.pruneEmptyGroups()">🧹 Clean Empty Groups</button>

						<button
							@click="toggleActionsPanel"
							class="btn btn-actions"
							:class="{ active: showActionsPanel }"
						>
							<span v-if="showActionsPanel">{{ __("Hide Actions") }}</span>
							<span v-else>{{ __("Show Actions") }}</span>
						</button>
						<button @click="store.addCondition" class="btn btn-add">
							<span v-html="utils.icon('plus', 'xs')"></span>
							{{ __("Add Condition") }}
						</button>
					</div>
				</div>

				<ConditionTree
					v-for="item in store.rootConditions"
					:key="item.condition_id"
					:condition-id="item.condition_id"
				/>
			</section>

			<transition name="slide-fade">
				<section v-if="showActionsPanel" class="actions">
					<div class="section-header">
						<h3>{{ __("Actions") }}</h3>
						<button @click="store.addAction" class="btn btn-add">
							<span v-html="utils.icon('plus', 'xs')"></span>
							{{ __("Add Action") }}
						</button>
					</div>
					<template v-if="store.actions.length === 0">
						<div class="empty-state">
							<p>{{ __("No actions defined yet") }}</p>
							<p>
								{{ __("Add actions to define what happens when conditions are met") }}
							</p>
						</div>
					</template>
					<template v-else>
						<Action :actions="store.actions" />
					</template>
				</section>
			</transition>
		</div>
		<div id="autocomplete-area" />

		<!-- Footer -->
		<div class="footer">
			<button @click="validateAndSave" class="btn btn-primary">
				{{ __("Save Rule") }}
			</button>
			<button @click="testRule" class="btn btn-secondary">
				{{ __("Test Rule") }}
			</button>
			<button @click="resetRule" class="btn btn-default">
				{{ __("Reset Changes") }}
			</button>
		</div>
	</div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useRuleBuilderStore } from "./store";

import Action from "./components/Action.vue";
import ConditionTree from "./components/ConditionTree.vue";
import Condition from "./components/Condition.vue";

import { safeFrappeUtils } from "./utils";

const store = useRuleBuilderStore();
const utils = safeFrappeUtils();

const showActionsPanel = ref(false);
const saveStatus = ref("idle");

const saveStatusClass = computed(() => ({
	"status-idle": saveStatus.value === "idle",
	"status-changed": saveStatus.value === "changed",
	"status-saving": saveStatus.value === "saving",
	"status-saved": saveStatus.value === "saved",
	"status-error": saveStatus.value === "error",
}));

const statusText = computed(() => {
	switch (saveStatus.value) {
		case "idle":
			return __("All changes saved");
		case "changed":
			return __("Unsaved changes");
		case "saving":
			return __("Saving...");
		case "saved":
			return __("Saved successfully");
		case "error":
			return __("Save failed");
		default:
			return "";
	}
});

function toggleActionsPanel() {
	showActionsPanel.value = !showActionsPanel.value;
}
function handleRemove(conditionId) {
	store.removeCondition(conditionId);
}

function handleDuplicate(conditionId) {
	store.duplicateInLayout(store.conditions.find((c) => c.condition_id === conditionId));
}

function handleReorder(event) {
	// Optional logic; may just be store-driven
	console.log("Reorder event triggered", event);
	store.reorderConditions([...store.conditions]);
}

function handleAddCondition(parentId) {
	store.addConditionToGroup({ condition_id: parentId });
}
function handleAddGroup(parentId) {
	store.addGroupToGroup({ condition_id: parentId });
}

function handleDragEnd({ moved, sourceGroupId, added, removed }) {
	if (!moved && !added && !removed) return;

	// moved: drag within same group (top or nested)
	// added/removed: drag across groups

	if (moved) {
		store.reorderConditions([...store.conditions]);
	} else if (added && removed) {
		const conditionId = added.element.condition_id;
		const newParent = sourceGroupId || null;
		const newIndex = added.newIndex;

		store.moveConditionBetweenGroups(conditionId, newParent, newIndex);
	}
}

async function validateAndSave() {
	const error = store.validateConditions();
	if (error) {
		frappe.msgprint({
			title: __("Validation Error"),
			message: error,
			indicator: "red",
		});
		return;
	}
	saveStatus.value = "saving";
	try {
		store.updateConditions();
		store.syncToForm();
		saveStatus.value = "saved";
		setTimeout(() => {
			if (saveStatus.value === "saved") saveStatus.value = "idle";
		}, 2000);
	} catch (err) {
		saveStatus.value = "error";
		frappe.msgprint({
			title: __("Save Error"),
			message: __("Error saving rule: {0}", [err.message]),
			indicator: "red",
		});
	}
}

function testRule() {
	if (saveStatus.value === "changed") {
		frappe.confirm(
			__("You have unsaved changes. Save before testing?"),
			() => validateAndSave().then(store.testRule),
			() => store.testRule(),
		);
	} else {
		store.testRule();
	}
}

function resetRule() {
	frappe.confirm(__("Are you sure you want to reset all changes?"), () => {
		store.syncFromForm();
		saveStatus.value = "idle";
	});
}

function collapseAll() {
	const ids = [];
	function collect(item) {
		if (item.condition_id) ids.push(item.condition_id);
		if (item.children?.length) item.children.forEach(collect);
	}
	store.layout.forEach(collect);
	store.collapseAll(ids);
}
</script>

<style scoped>
.rule-builder {
	padding: 1.5rem;
	background: #f9fafb;
	border-radius: 8px;
	min-height: 80vh;
	display: flex;
	flex-direction: column;
}
.header.hidden {
	transform: translateY(-100%);
	transition: transform 0.3s;
	position: fixed;
	top: 0;
	width: 100%;
	background: white;
	z-index: 20;
	box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin: -15px -20px -5px;
	flex-wrap: wrap;
	gap: 1rem;
}

.controls {
	display: flex;
	gap: 1rem;
	align-items: center;
	flex-wrap: wrap;
}

.status-indicators {
	display: flex;
	align-items: center;
	gap: 1rem;
}

.save-status {
	padding: 0.3rem 1rem;
	border-radius: 1rem;
	font-size: 0.9rem;
	font-weight: 500;
}

.status-idle {
	background: #e5f6e5;
	color: #1a7f37;
}

.status-changed {
	background: #fef7e0;
	color: #b95000;
}

.status-saving {
	background: #e0f2fe;
	color: #0b5fff;
}

.status-saved {
	background: #d1fae5;
	color: #065f46;
}

.status-error {
	background: #fde2e2;
	color: #da1414;
}

.validation-error.floating-alert {
	position: fixed;
	top: 1rem;
	left: 50%;
	transform: translateX(-50%);
	z-index: 1000;
	max-width: 90%;
	width: max-content;
}

.alert-content {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	padding: 0.75rem 1.25rem;
	background: #fef2f2;
	color: #b91c1c;
	border-radius: 8px;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.close-btn {
	margin-left: auto;
	background: none;
	border: none;
	color: inherit;
	cursor: pointer;
	padding: 0.25rem;
	border-radius: 50%;
	width: 24px;
	height: 24px;
	display: flex;
	align-items: center;
	justify-content: center;
}

.close-btn:hover {
	background: rgba(0, 0, 0, 0.05);
}

.builder-container {
	display: flex;
	flex-direction: column;
	flex: 1;
	margin: -15px -20px -5px;
	transition: all 0.3s ease;
}

.builder-container.actions-visible {
	flex-direction: row;
	gap: 1.5rem;
}

section {
	background: white;
	padding: 1rem;
	border: 1px solid #e5e7eb;
	border-radius: 8px;
	box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.conditions {
	flex: 1;
	margin: -15px -20px -5px;

	transition: all 0.3s ease;
}

.builder-container.actions-visible .conditions {
	flex: 2;
}

.actions {
	flex: 1;
	min-width: 300px;
	max-width: 40%;
	transition: all 0.3s ease;
}

.section-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 1rem;
	position: sticky;
	top: 0;
	background: white;
	z-index: 10;
	padding: 0.5rem 0;
	border-bottom: 1px solid #e5e7eb;
}

.group-actions {
	display: flex;
	gap: 0.5rem;
}

.empty-state {
	padding: 2rem;
	text-align: center;
	color: #6b7280;
	border: 2px dashed #e5e7eb;
	border-radius: 8px;
	margin-top: 1rem;
}

.empty-state p {
	margin: 0.5rem 0;
}

.footer {
	margin-top: auto;
	display: flex;
	justify-content: flex-end;
	gap: 1rem;
	flex-wrap: wrap;
}

.btn {
	padding: 0.5rem 1rem;
	border: none;
	border-radius: 6px;
	cursor: pointer;
	font-weight: 500;
	transition: all 0.2s;
	display: inline-flex;
	align-items: center;
	gap: 0.5rem;
}

.btn-add {
	background: #e0f2fe;
	color: #0369a1;
}

.btn-actions {
	background: #ede9fe;
	color: #7c3aed;
	font-weight: 600;
}

.btn-actions.active {
	background: #ddd6fe;
}

.btn-primary {
	background: #2563eb;
	color: white;
}

.btn-secondary {
	background: #6b7280;
	color: white;
}

.btn-default {
	background: #f3f4f6;
	color: #4b5563;
}

.btn:hover {
	opacity: 0.9;
	transform: translateY(-1px);
}

/* New styles */
.condition-item {
	margin-bottom: 1rem;
	border: 1px solid #e5e7eb;
	border-radius: 8px;
	padding: 1rem;
	background: white;
	position: relative;
}

.condition-group {
	background: #f0f9ff;
	border-color: #bae6fd;
}

.condition-row {
	background: #f8fafc;
	border-color: #e2e8f0;
}

.nested {
	margin-left: 2rem;
	border-left: 3px solid #dbeafe;
}

.item-toolbar {
	display: flex;
	justify-content: flex-start;
	align-items: center;
	gap: 0.5rem;
	margin-bottom: 0.5rem;
	padding-bottom: 0.5rem;
	border-bottom: 1px solid #f3f4f6;
}

.group-type-badge {
	margin-left: auto;
	padding: 0.25rem 0.5rem;
	background: #dbeafe;
	color: #1d4ed8;
	border-radius: 4px;
	font-size: 0.75rem;
	font-weight: 500;
}

.dragging-ghost {
	opacity: 0.7;
	transform: scale(1.02);
	box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.empty-conditions {
	padding: 3rem;
	text-align: center;
	border: 2px dashed #e5e7eb;
	border-radius: 8px;
	margin-top: 1rem;
}

.empty-content {
	max-width: 400px;
	margin: 0 auto;
}

.empty-content span {
	display: block;
	margin-bottom: 1rem;
	color: #d1d5db;
}

/* Animation for actions panel */
.slide-fade-enter-active {
	transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
	transition: all 0.3s ease-in;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
	opacity: 0;
	transform: translateX(20px);
}

/* Responsive design */
@media (max-width: 1024px) {
	.builder-container.actions-visible {
		flex-direction: column;
		gap: 1.5rem;
	}

	.actions {
		max-width: 100%;
		min-width: auto;
	}
}

@media (max-width: 768px) {
	.header {
		flex-direction: column;
		align-items: flex-start;
	}

	.controls {
		width: 100%;
		justify-content: space-between;
	}

	.section-header {
		flex-direction: column;
		align-items: flex-start;
		gap: 0.5rem;
	}

	.group-actions {
		width: 100%;
		justify-content: flex-end;
	}

	.condition-item {
		padding: 0.75rem;
	}

	.nested {
		margin-left: 1rem;
	}

	.item-toolbar {
		flex-wrap: wrap;
	}

	.group-type-badge {
		order: -1;
		width: 100%;
		margin-bottom: 0.5rem;
		text-align: center;
	}

	.footer {
		justify-content: center;
	}

	.btn {
		width: 100%;
		justify-content: center;
		margin-bottom: 0.5rem;
	}
}
</style>
