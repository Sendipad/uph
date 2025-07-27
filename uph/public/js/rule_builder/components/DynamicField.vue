<script setup>
import { computed, ref, reactive, defineExpose } from "vue";

import { evaluate_depends_on_value } from "../utils.js";
import LinkAutocomplete from "./LinkAutocomplete.vue";
import FieldSelector from "./FieldSelector.vue";
import { useRuleBuilderStore } from "../store.js";
import DocFieldCrawl from "./DocFieldCrawl.vue";

const props = defineProps({
	df: Object,
	doc: Object,
	mode: { type: String, default: "default" }, // 'default', 'compact', 'grid', 'labelless'
});

const isFocused = ref(false);

const showFloatingLabel = computed(
	() => props.mode === "compact" && props.df.fieldtype !== "Check" && props.df.label,
);
const docFieldCrawlRef = ref(null);

const emit = defineEmits(["update:modelValue"]);
const store = useRuleBuilderStore();
const showLabel = computed(() => {
	if (props.mode === "labelless") return false;
	if (props.mode === "compact") return props.df.fieldtype !== "Check";
	return true;
});

const labelInsideInput = computed(() => {
	return props.mode === "compact" && !showLabel.value;
});

const inputClass = computed(() => {
	let cls = "input-base";
	if (props.mode === "grid") cls += " grid-mode";
	else if (props.mode === "compact") cls += " compact-mode";
	return cls;
});

const value = computed({
	get: () => props.doc?.[props.df.fieldname],
	set: (val) => {
		props.doc[props.df.fieldname] = val;
		emit("update:modelValue", val);
	},
});

const parentDoc = computed(() => props.doc?.__parent || store.doc || {});
const isVisible = computed(() =>
	evaluate_depends_on_value(props.df.depends_on, props.doc, parentDoc.value),
);

const isRequired = computed(() =>
	evaluate_depends_on_value(props.df.mandatory_depends_on, props.doc, parentDoc.value),
);

const isReadOnly = computed(() =>
	evaluate_depends_on_value(props.df.read_only_depends_on, props.doc, parentDoc.value),
);

// Fieldtype mapping for input types
const inputType = computed(() => {
	switch (props.df.fieldtype) {
		case "Int":
			return "number";
		case "Float":
		case "Currency":
			return "number";
		case "Date":
			return "date";
		default:
			return "text";
	}
});

// Options for Select
const parsedOptions = computed(() => {
	if (Array.isArray(props.df.options)) return props.df.options;
	if (typeof props.df.options === "string") {
		return props.df.options.split("\n").filter((opt) => opt.trim() !== "");
	}
	return [];
});
const fieldSourceDoctypes = computed(() => {
	const source =
		props.doc[
			props.df.fieldname === "left_field_path" ? "left_value_source" : "right_value_source"
		];

	if (source === "Specific DocType Field") {
		return props.doc[
			props.df.fieldname === "left_field_path" ? "left_specific_doctype" : "right_specific_doctype"
		];
	}

	// fallback to parent provided documentTypes (from store)
	return store.documentTypes;
});
defineExpose({
	get_value() {
		// If the inner DocFieldCrawl component has get_value, use it
		if (docFieldCrawlRef.value?.get_value) {
			return docFieldCrawlRef.value.get_value();
		}
		// Otherwise, fallback to raw string render
		const val = value.value;
		if (typeof val === "object" && Array.isArray(val?.field_chain)) {
			return val.field_chain.map((f) => f.label || f.fieldname).join(" › ");
		}
		return "";
	},
});
</script>
<template>
	<div
		class="field-wrapper"
		v-show="isVisible"
		:class="[
			mode === 'compact' ? 'field-compact' : '',
			mode === 'labelless' ? 'field-labelless' : '',
			df.fieldtype === 'Check' ? 'field-check' : '',
		]"
	>
		<!-- Checkbox Inline -->
		<template v-if="df.fieldtype === 'Check'">
			<label class="checkbox-inline">
				<input type="checkbox" v-model="value" :disabled="isReadOnly" />
				<span>{{ df.label }}</span>
				<span v-if="isRequired" class="required-indicator">*</span>
			</label>
		</template>

		<!-- Normal Label (only if not labelless or compact mode with placeholder) -->
		<label
			v-else-if="showLabel"
			class="field-label"
			:class="{ bold: df.bold, required: isRequired }"
		>
			{{ df.label }}
			<span v-if="isRequired" class="required-indicator">*</span>
		</label>

		<!-- Select -->
		<select v-if="df.fieldtype === 'Select'" v-model="value" :disabled="isReadOnly">
			<option v-if="!isRequired" value="">-{{ __("Select") + __(df.label) }}-</option>
			<option v-for="opt in parsedOptions" :key="opt" :value="opt">{{ opt }}</option>
		</select>

		<!-- Textarea -->
		<textarea
			v-else-if="df.fieldtype === 'Text'"
			v-model="value"
			:readonly="isReadOnly"
			:placeholder="placeholderText"
		></textarea>

		<!-- Link -->
		<LinkAutocomplete
			v-else-if="df.fieldtype === 'Link'"
			v-model="value"
			:doctype="df.options"
			:disabled="isReadOnly"
		/>

		<!-- Autocomplete -->
		<FieldSelector
			v-else-if="df.fieldtype === 'Autocomplete'"
			v-model="value"
			:documentType="fieldSourceDoctypes"
			:disabled="isReadOnly"
		/>

		<!-- Default Input -->
		<div class="input-wrapper" v-else>
			<input
				:type="inputType"
				v-model="value"
				:readonly="isReadOnly"
				@focus="isFocused = true"
				@blur="isFocused = false"
			/>
			<label
				v-if="showFloatingLabel"
				class="floating-label"
				:class="{ active: isFocused || !!value }"
			>
				{{ df.label }}
			</label>
		</div>
	</div>
</template>

<style scoped>
.field-wrapper {
	display: flex;
	flex-direction: column;
	margin-bottom: 1rem;
}

.field-label {
	font-size: 0.85rem;
	margin-bottom: 0.25rem;
	color: #374151;
}

.field-label.bold {
	font-weight: bold;
}

.required-indicator {
	color: #dc2626;
	margin-left: 0.25rem;
}
.field-wrapper {
	display: flex;
	flex-direction: column;
	margin: 0.25rem 0;
	gap: 0.25rem;
	font-size: 0.875rem;
}

.field-label {
	font-size: 0.75rem;
	color: #4b5563;
	display: flex;
	align-items: center;
	gap: 0.25rem;
}
.field-wrapper.field-compact,
.field-wrapper.field-labelless {
	margin-bottom: 0.25rem;
}

.checkbox-inline {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	font-size: 0.875rem;
}

.field-wrapper input,
.field-wrapper select,
.field-wrapper textarea {
	padding: 0.25rem 0.5rem;
	font-size: 0.8rem;
}

.field-wrapper.field-compact label.field-label,
.field-wrapper.field-labelless label.field-label {
	display: none;
}

.field-label.bold {
	font-weight: 600;
}

.required-indicator {
	color: #dc2626;
	font-weight: bold;
}

input,
select,
textarea {
	font-size: 0.85rem;
	padding: 0.25rem 0.5rem;
	border: 1px solid #d1d5db;
	border-radius: 0.375rem;
	width: 100%;
	box-sizing: border-box;
}
</style>
