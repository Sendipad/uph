<script setup>
import { computed } from "vue";
import DynamicField from "./DynamicField.vue";

const props = defineProps({
	doc: Object,
	fields: Array,
	layoutMode: {
		type: String,
		default: "default", // options: 'default', 'compact', 'grid', 'labelless'
	},
});

function parseLayout(fields) {
	const layout = [];
	let currentSection = { type: "Section Break", label: null, columns: [[]] };
	let currentColumnIndex = 0;

	for (const f of fields) {
		if (f.fieldtype === "Section Break") {
			if (hasFields(currentSection)) {
				layout.push(cleanSection(currentSection));
			}
			currentSection = { type: "Section Break", label: f.label || null, columns: [[]] };
			currentColumnIndex = 0;
		} else if (f.fieldtype === "Column Break") {
			currentSection.columns.push([]);
			currentColumnIndex = currentSection.columns.length - 1;
		} else {
			currentSection.columns[currentColumnIndex].push(f);
		}
	}

	if (hasFields(currentSection)) {
		layout.push(cleanSection(currentSection));
	}

	return layout;
}

function cleanSection(section) {
	const nonEmptyColumns = section.columns.filter((col) =>
		col.some((f) => f.fieldtype !== "Section Break" && f.fieldtype !== "Column Break"),
	);
	return { ...section, columns: nonEmptyColumns };
}

function hasFields(section) {
	return section.columns.some((col) =>
		col.some((f) => f.fieldtype !== "Section Break" && f.fieldtype !== "Column Break"),
	);
}

const parsedLayout = computed(() => parseLayout(props.fields));
</script>
<template>
	<div class="form-layout">
		<template v-if="parsedLayout.length">
			<div v-for="(section, sIndex) in parsedLayout" :key="sIndex" class="form-section">
				<h4 v-if="section.label" class="section-label">{{ section.label }}</h4>
				<div class="columns">
					<div v-for="(column, cIndex) in section.columns" :key="cIndex" class="form-column">
						<DynamicField
							v-for="df in column"
							:key="df.fieldname"
							:df="df"
							:doc="doc"
							:mode="layoutMode"
							@update:modelValue="(val) => (doc[df.fieldname] = val)"
						/>
					</div>
				</div>
			</div>
		</template>
		<div v-else class="empty-state">
			<p>No fields to display.</p>
		</div>
	</div>
</template>
<style scoped>
.form-layout {
	display: flex;
	flex-direction: column;
	gap: 1.25rem;
}

.form-section {
	padding-top: 0.25rem;
}

.section-label {
	font-size: 1rem;
	font-weight: 600;
	margin-bottom: 0.5rem;
	color: #374151;
}

.columns {
	display: flex;
	flex-wrap: wrap;
	gap: 1rem;
}

.form-column {
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 0.75rem;
}

.empty-state {
	text-align: center;
	color: #9ca3af;
	font-style: italic;
}
</style>
