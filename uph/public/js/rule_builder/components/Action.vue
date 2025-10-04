<template>
	<div class="action">
		<div v-if="localActions.length === 0" class="no-actions">
			{{ __("No actions defined yet. Click 'Add Action' to create one.") }}
		</div>

		<EditableGrid
			v-model="localActions"
			:columns="columns"
			new-row-mode="grid"
			@update:modelValue="onActionsUpdate"
			@row-added="onActionRowAdded"
			@cell-edited="onActionCellEdited"
			@row-removed="(removedRow) => emit('remove', removedRow.name)"
		/>
	</div>
</template>
<script setup>
import EditableGrid from "./EditableGrid.vue";
import { safeFrappeUtils, loadDoctypeFields } from "../utils";

defineProps({
	actions: {
		type: Array,
		default: () => [],
	},
});
const emit = defineEmits(["update", "remove"]);
const utils = safeFrappeUtils();
const actionFields = ref([]);
async function loadActionFields() {
	let fields = await loadDoctypeFields("Rule Action", {});

	actionFields.value = fields;
}

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
	const dynamicColumns = actionFields.value.map((f) => ({
		fieldname: f.fieldname,
		label: f.label,
		width: f.width || 120,
		fieldtype: f.fieldtype,
		options: f.options,
		read_only: f.read_only,
		mandatory: f.reqd,
	}));

	return [...baseColumns, ...dynamicColumns];
});
</script>

<style scoped>
.action {
	display: flex;
	flex-direction: column;
	gap: 12px;
}

.no-actions {
	text-align: center;
	padding: 20px;
	background: #f9fafb;
	border: 1px dashed #d1d5db;
	border-radius: 6px;
	color: #6b7280;
}
</style>
