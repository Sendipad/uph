<template>
	<div class="action-group">
		<div v-if="actions.length === 0" class="no-actions">
			{{ __("No actions defined yet. Click 'Add Action' to create one.") }}
		</div>

		<ActionRow
			v-for="(action, index) in actions"
			:key="action.name || index"
			:action="action"
			@update="$emit('update')"
			@remove="$emit('remove', action.name)"
		/>
	</div>
</template>

<script setup>
import ActionRow from "./ActionRow.vue";

defineProps({
	actions: {
		type: Array,
		default: () => [],
	},
});
</script>

<style scoped>
.action-group {
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
