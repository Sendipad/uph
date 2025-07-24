<template>
	<div class="action-row">
		<div class="action-type">
			<select v-model="action.action_type" @change="updateAction">
				<option v-for="type in actionTypes" :key="type" :value="type">
					{{ __(type) }}
				</option>
			</select>
		</div>

		<div class="action-details" v-if="showTargetField">
			<FieldSelector
				v-model="action.target_field"
				:document-type="documentType"
				@change="updateAction"
				:placeholder="__('Target field')"
			/>
		</div>

		<div class="action-value" v-if="showValueField">
			<input
				v-model="action.action_value_data"
				@input="updateAction"
				:placeholder="valueFieldPlaceholder"
			/>
		</div>

		<div class="action-actions">
			<button @click="$emit('remove')" class="remove-btn" title="Remove action">✕</button>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import FieldSelector from "./FieldSelector.vue";

const props = defineProps({
	action: {
		type: Object,
		required: true,
	},
	documentType: String,
});

const emit = defineEmits(["update", "remove"]);

const actionTypes = computed(() => [
	"Set Field Value",
	"Notify Users",
	"Raise Alert (Error)",
	"Call Method",
	"Create Document",
]);

const showTargetField = computed(() =>
	["Set Field Value", "Raise Alert (Error)"].includes(props.action.action_type),
);

const showValueField = computed(() =>
	["Set Field Value", "Notify Users"].includes(props.action.action_type),
);

const valueFieldPlaceholder = computed(() =>
	props.action.action_type === "Set Field Value" ? __("Enter value") : __("Enter message"),
);

function updateAction() {
	emit("update");
}
</script>

<style scoped>
.action-row {
	display: grid;
	grid-template-columns: 1.5fr 2fr 2fr auto;
	gap: 10px;
	align-items: center;
	padding: 10px;
	border: 1px solid #e5e7eb;
	border-radius: 6px;
	background: white;
}

.action-type select {
	width: 100%;
}

.action-details,
.action-value {
	display: flex;
}

.remove-btn {
	background: none;
	border: none;
	color: #ef4444;
	cursor: pointer;
	font-size: 1.2rem;
	padding: 0 5px;
}
</style>
