<script setup>
import { ref, computed, onMounted } from "vue";
import { useRuleBuilderStore } from "../store";
import { safeFrappeUtils, loadDoctypeFields } from "../utils";
import NestedEditableGrid from "./NestedEditableGrid.vue";
import DynamicField from "./DynamicField.vue";

const store = useRuleBuilderStore();
const utils = safeFrappeUtils();

// Constants
const groupingKeyField = "is_group";
const operatorOptions = ["=", "!=", ">", "<", ">=", "<=", "in", "not in", "like", "not like"];

// Fields to exclude completely
const excludedFieldnames = new Set([
	"is_group",
	"condition_id",
	"parent_condition_id",
	"group_a_column",
	"group_b_column",
	"group_logic_section",
	"indent",
	"group_operator",
	"logical_operator",
	"condition_section",
]);

// Field types to exclude
const excludedFieldtypes = new Set(["Column Break", "Section Break", "Tab Break"]);

// Reactive state
const conditionFields = ref([]);
const fieldOptions = computed(() => store.getAvailableFields());

// Load condition fields from Frappe meta
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
async function loadConditionFields() {
	let fields = await loadDoctypeFields("Rule Condition", {
		excludedFieldnames: blacklist,
	});
	fields = fields.filter((f) => {
		const depends = f.depends_on || "";
		const isGroupOnly = /doc\.is_group\s*={1,3}\s*1/.test(depends);
		return !isGroupOnly;
	});

	conditionFields.value = fields;
}

// Dynamic columns configuration
const columns = computed(() => {
	const baseColumns = [
		{
			fieldname: "selection",
			label: "",
			width: 40,
			slotName: "selection-cell",
			showInSummary: false,
		},
		{
			fieldname: "drag",
			label: "",
			width: 40,
			slotName: "drag-cell",
			showInSummary: false,
		},
		{
			fieldname: "operator",
			label: "Operator",
			width: 100,
			slotName: "operator-cell",
			showInSummary: true,
		},
		{
			fieldname: "content",
			label: "Condition",
			width: 400,
			slotName: "condition-content",
			showInSummary: true,
		},
		{
			fieldname: "actions",
			label: "Actions",
			width: 150,
			slotName: "condition-actions",
			showInSummary: false,
		},
	];

	// Add dynamic fields as columns
	const dynamicColumns = conditionFields.value.map((f) => ({
		fieldname: f.fieldname,
		label: f.label,
		width: f.width || 120,
		fieldtype: f.fieldtype,
		options: f.options,
		read_only: f.read_only,
		mandatory: f.reqd,
		showInSummary: ["left_field_path", "operator", "right_field_path"].includes(f.fieldname),
	}));

	return [...baseColumns, ...dynamicColumns];
});

// Prepare rows data for the grid
const gridRows = computed(() => {
	return store.conditions.map((c) => ({
		...c,
		isAnd: c.group_operator === "AND", // sync for group toggle
	}));
});

// Group actions
const groupActions = [
	{ label: "Add Condition", key: "add-condition", icon: utils.icon("plus", "sm") },
	{ label: "Add Group", key: "add-group", icon: utils.icon("folder-add", "sm") },
];

// Event handlers
const handleDragDrop = ({ draggedRow, targetRow }) => {
	store.moveCondition(draggedRow.condition_id, targetRow?.condition_id || "Root");
};

const handleGroupAction = (action, group) => {
	if (action.key === "add-condition") {
		const c = store.addCondition(group.condition_id);
		if (c) store.focusCondition(c.condition_id);
	} else if (action.key === "add-group") {
		const g = store.addGroup(group.condition_id);
		if (g) store.focusCondition(g.condition_id);
	}
};

const handleGroupToggle = (group, expanded) => {
	store.setConditionCollapsed(group.condition_id, !expanded);
};

const handleCellEdit = ({ row, fieldname, value }) => {
	store.updateConditionField(row.condition_id, fieldname, value);
	store.markDirty();
};

const handleRowRemove = (row) => {
	if (row.condition_id === "Root") {
		frappe.confirm("Delete all conditions?", () => {
			store.removeCondition(row.condition_id);
		});
	} else {
		store.removeCondition(row.condition_id);
	}
};

const updateField = (row, field, value) => {
	row[field] = value;
	store.updateConditionField(row.condition_id, field, value);
	store.markDirty();
};

const duplicateCondition = (row) => {
	const d = store.duplicateInLayout(row);
	if (d) store.focusCondition(d.condition_id);
};

const toggleRowSelection = (row) => {
	if (row.is_group) {
		store.setGroupSelected(row.condition_id, !store.isConditionSelected(row.condition_id));
	} else {
		store.setConditionSelected(row.condition_id, !store.isConditionSelected(row.condition_id));
	}
};

const isRowSelected = (row) => store.isConditionSelected(row.condition_id);
function getSummaryFields(row) {
	if (!row || !conditionFields.value.length) return [];
	const fields = [];

	const leftField = conditionFields.value.find((f) => f.fieldname === "left_field_chain");
	const operatorField = conditionFields.value.find((f) => f.fieldname === "operator");

	if (leftField) fields.push(leftField);
	if (operatorField) fields.push(operatorField);

	conditionFields.value.forEach((f) => {
		if (f.reqd && row[f.fieldname] != null && row[f.fieldname] !== "") {
			fields.push(f);
		}
	});
	return fields.slice(0, 4);
}

onMounted(() => {
	loadConditionFields();
});
</script>

<template>
	<NestedEditableGrid :columns="columns" :rows="rows" @update:rows="rows = $event">
		<template #item_code-cell="{ row, isEditing, startEditing, stopEditing }">
			<div v-if="isEditing">
				<CustomAutocomplete
					v-model="row.item_code"
					:options="itemCodeOptions"
					:autoFocus="true"
					@commit-edit="stopEditing"
				/>
			</div>
			<div v-else @dblclick="startEditing">
				{{ row.item_code }}
			</div>
		</template>
	</NestedEditableGrid>
</template>

<style scoped>
/* Add your custom styles here */
.drag-handle {
	cursor: grab;
	opacity: 0.3;
	transition: opacity 0.2s;
}
.drag-handle:hover {
	opacity: 0.8;
}

.condition-content {
	display: flex;
	align-items: center;
	gap: 8px;
}

.group-icon {
	margin-right: 8px;
	color: #f59e0b;
}

.child-count {
	margin-left: 8px;
	color: #64748b;
	font-size: 0.9em;
}

.condition-actions {
	display: flex;
	gap: 8px;
}

.condition-actions button {
	background: none;
	border: none;
	cursor: pointer;
	padding: 4px;
}

.condition-actions button.danger {
	color: #ef4444;
}

/* Group switch styles (similar to your original) */
.group-switch {
	position: relative;
	width: 60px;
	height: 24px;
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
	background-color: #f1f5f9;
	border: 1px solid #e2e8f0;
	transition: all 0.15s ease;
}

.switch-thumb {
	position: absolute;
	top: 2px;
	left: 2px;
	width: 18px;
	height: 18px;
	border-radius: 50%;
	background-color: white;
	box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
	transition: transform 0.15s ease;
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
	color: #64748b;
	transition: color 0.15s ease;
}

.is-and .switch-thumb {
	transform: translateX(36px);
	background-color: #10b981;
}

.is-and .label-and {
	color: #10b981;
	font-weight: 700;
}

.is-or .switch-thumb {
	transform: translateX(2px);
	background-color: #f59e0b;
}

.is-or .label-or {
	color: #f59e0b;
	font-weight: 700;
}
</style>
