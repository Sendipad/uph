<script setup>
import { Combobox, ComboboxInput, ComboboxOptions, ComboboxOption } from "@headlessui/vue";
import { ref, computed, reactive, watch } from "vue";
import { safeFrappeUtils } from "../utils";

const utils = safeFrappeUtils();

const props = defineProps({
	modelValue: [String, Object], // string for flat, object for recursive
	documentType: [String, Array],
	placeholder: { type: String, default: "Select Field" },
	disabled: Boolean,
	recursive: { type: Boolean, default: false }, // new prop to toggle mode
});

const emit = defineEmits(["update:modelValue", "change"]);

const isLoading = ref(false);
const loadError = ref(false);

// For recursive mode
const levels = ref([]);
const showOptions = reactive([]);
const fieldChain = ref([]);
const baseDoctype = ref(null);

// For flat mode
const fieldOptions = ref([]);
const selectedOption = ref(null);
const query = ref("");
const showFlatOptions = ref(false);

// --- Common Functions ---

function getFieldIcon(type) {
	return (
		{
			Data: "edit",
			Link: "link",
			Select: "arrow-down",
			Date: "calendar",
			Int: "hash",
			Check: "check-square",
			Currency: "dollar-sign",
			Float: "percent",
			Text: "align-left",
		}[type] || "circle"
	);
}
const filteredFieldsFlat = computed(() => {
	if (!query.value) return fieldOptions.value;

	const term = query.value.toLowerCase();
	return fieldOptions.value.filter((f) => (f.label || f.fieldname).toLowerCase().includes(term));
});
// --- Backend API wrapper (simulate) ---
async function getDocfieldsAsync(document_type, basefieldname = null) {
	if (
		!document_type ||
		(Array.isArray(document_type) && document_type.length === 0) ||
		(typeof document_type === "string" && document_type.trim() === "")
	) {
		// Return empty fields instead of calling backend when no valid doctype
		return { fields: [] };
	}
	return new Promise((resolve) => {
		uph.hub.docfields.get_docfields(document_type, basefieldname, resolve);
	});
}

// --- Recursive mode logic ---

async function resolveCommonFields(doctype) {
	if (Array.isArray(doctype)) {
		const result = await getDocfieldsAsync(doctype);
		return { doctype: "_MULTI", fields: result.fields || [] };
	} else {
		return await loadDoctypeFields(doctype);
	}
}

async function loadDoctypeFields(doctype, basefield = null) {
	const result = await getDocfieldsAsync(doctype, basefield);
	return { doctype, fields: result.fields || [] };
}

async function pushLevel(source) {
	levels.value.push({
		doctype: source.doctype,
		fields: source.fields,
		selected: "",
		query: "",
	});
	showOptions.push(true);
}

function filteredFields(index) {
	const q = levels.value[index]?.query?.toLowerCase() || "";
	return (
		levels.value[index]?.fields?.filter((f) =>
			(f.label || f.fieldname).toLowerCase().includes(q),
		) || []
	);
}

function getLabel(index, fieldname) {
	return levels.value[index]?.fields?.find((f) => f.fieldname === fieldname)?.label || fieldname;
}

function handleBlur(index) {
	setTimeout(() => {
		showOptions[index] = false;
	}, 200);
}

async function onSelect(index, fieldname) {
	const level = levels.value[index];
	level.selected = fieldname;

	// Remove deeper levels
	levels.value.splice(index + 1);
	showOptions.splice(index + 1);
	fieldChain.value.splice(index);

	const field = level.fields.find((f) => f.fieldname === fieldname);
	if (!field) return;

	fieldChain.value.push(field);

	// Expand next level if applicable
	if (field.fieldtype === "Link") {
		const childFields = await loadDoctypeFields(field.options);
		await pushLevel(childFields);
	} else if (field.fieldtype === "Table") {
		const childFields = await loadDoctypeFields(baseDoctype.value, field.fieldname);
		await pushLevel(childFields);
	}

	emitChangeRecursive();
}

function emitChangeRecursive() {
	const chain = fieldChain.value.map((f) => ({
		fieldname: f.fieldname,
		fieldtype: f.fieldtype,
		label: f.label,
		options: f.options || null,
	}));

	emit("update:modelValue", {
		document_type: props.documentType,
		field_chain: chain,
	});
	emit("change", {
		document_type: props.documentType,
		field_chain: chain,
	});
}

async function initFromChain(chain) {
	levels.value = [];
	fieldChain.value = [];

	let current = await resolveCommonFields(baseDoctype.value);

	for (const fieldObj of chain) {
		await pushLevel(current);
		const level = levels.value.at(-1);
		level.selected = fieldObj.fieldname;

		const field = level.fields.find((f) => f.fieldname === fieldObj.fieldname);
		if (!field) break;

		fieldChain.value.push(field);

		if (field.fieldtype === "Link") {
			current = await loadDoctypeFields(field.options);
		} else if (field.fieldtype === "Table") {
			current = await loadDoctypeFields(baseDoctype.value, field.fieldname);
		} else {
			break;
		}
	}
}

// --- Flat mode logic ---

async function loadFlatOptions() {
	if (!props.documentType) return;

	isLoading.value = true;
	loadError.value = false;

	try {
		const normalizedTypes = Array.isArray(props.documentType)
			? [...new Set(props.documentType)].sort()
			: [props.documentType];

		const fields = await getDocfieldsAsync(normalizedTypes);

		fieldOptions.value = fields.fields || [];

		updateSelectedOption();
	} catch (e) {
		console.error("Field load failed:", e);
		loadError.value = true;
		fieldOptions.value = [];
	} finally {
		isLoading.value = false;
	}
}

function updateSelectedOption() {
	if (!props.modelValue) {
		selectedOption.value = null;
		return;
	}

	if (props.recursive) {
		// in recursive mode, modelValue is object — no flat selection
		selectedOption.value = null;
	} else {
		// flat mode, modelValue is string
		selectedOption.value = fieldOptions.value.find((f) => f.fieldname === props.modelValue) || null;
	}
}

function onSelectFlat(option) {
	selectedOption.value = option;
	emit("update:modelValue", option?.fieldname || "");
	emit("change", option?.fieldname || "");
}

function handleBlurFlat() {
	setTimeout(() => {
		showFlatOptions.value = false;
	}, 200);
}

// --- Watchers ---

watch(
	() => props.modelValue,
	(val) => {
		if (props.recursive) {
			if (!val?.field_chain) return;
			initFromChain(val.field_chain);
		} else {
			updateSelectedOption();
		}
	},
	{ immediate: true },
);

watch(
	() => props.documentType,
	() => {
		// Defensive check for valid documentType
		if (
			!props.documentType ||
			(Array.isArray(props.documentType) && props.documentType.length === 0) ||
			(typeof props.documentType === "string" && props.documentType.trim() === "")
		) {
			// Clear state and skip loading fields if no valid doctype
			baseDoctype.value = null;
			levels.value = [];
			fieldChain.value = [];
			return;
		}

		baseDoctype.value = props.documentType;

		if (props.recursive) {
			initFromChain([]);
		} else {
			loadFlatOptions();
		}
	},
	{ immediate: true },
);
</script>

<template>
	<div class="docfield-crawl">
		<div v-if="props.recursive">
			<div class="field-chain">
				<template v-for="(item, index) in fieldChain" :key="index">
					<span class="field-item">
						<span v-html="utils.icon(getFieldIcon(item.fieldtype), 'xs')"></span>
						{{ item.label || item.fieldname }}
					</span>
					<span v-if="index < fieldChain.length - 1" class="arrow">›</span>
				</template>
			</div>

			<div v-for="(level, index) in levels" :key="index">
				<Combobox
					:modelValue="level.selected"
					@update:modelValue="(val) => onSelect(index, val)"
					:disabled="disabled"
				>
					<div class="combo-container">
						<ComboboxInput
							class="combo-input"
							:placeholder="index === 0 ? placeholder : 'Next field...'"
							@input="level.query = $event.target.value"
							@focus="showOptions[index] = true"
							@blur="() => handleBlur(index)"
							:displayValue="(val) => getLabel(index, val)"
						/>

						<ComboboxOptions v-show="showOptions[index]" static class="combo-options">
							<ComboboxOption
								v-for="field in filteredFields(index)"
								:key="field.fieldname"
								:value="field.fieldname"
								as="template"
								v-slot="{ active, selected }"
							>
								<div :class="{ 'combo-option': true, active, selected }">
									<span v-html="utils.icon(getFieldIcon(field.fieldtype), 'xs')"></span>
									<span>{{ field.label || field.fieldname }}</span>
								</div>
							</ComboboxOption>
							<div v-if="!filteredFields(index).length" class="empty-state">
								{{ __("No matching fields") }}
							</div>
						</ComboboxOptions>
					</div>
				</Combobox>
			</div>
		</div>

		<div v-else>
			<!-- Loading -->
			<div v-if="isLoading" class="field-loading">
				<span class="spinner"></span>
				{{ __("Loading fields...") }}
			</div>

			<!-- Error -->
			<div v-else-if="loadError" class="field-error">
				<span v-html="utils.icon('warning', 'sm')"></span>
				{{ __("Error loading fields") }}
			</div>

			<!-- Flat single-level Combobox -->
			<Combobox :modelValue="selectedOption" @update:modelValue="onSelectFlat" :disabled="disabled">
				<div class="relative">
					<ComboboxInput
						class="combobox-input"
						:placeholder="placeholder"
						:displayValue="(item) => item?.label || ''"
						@input="query = $event.target.value"
						@focus="showFlatOptions = true"
						@blur="handleBlurFlat"
					/>

					<ComboboxOptions v-show="showFlatOptions" static class="combobox-options">
						<ComboboxOption
							v-for="field in filteredFieldsFlat"
							:key="field.fieldname"
							:value="field"
							as="template"
							v-slot="{ active, selected }"
						>
							<div
								class="combobox-option"
								:class="{ 'option-active': active, 'option-selected': selected }"
							>
								<span v-html="utils.icon(getFieldIcon(field.fieldtype), 'xs')"></span>
								<span>{{ field.label || field.fieldname }}</span>
							</div>
						</ComboboxOption>

						<div v-if="!filteredFieldsFlat.length" class="empty-state">
							{{ __("No matching fields") }}
						</div>
					</ComboboxOptions>
				</div>
			</Combobox>
		</div>
	</div>
</template>

<style scoped>
.docfield-crawl {
	display: flex;
	flex-direction: column;
	gap: 0.75rem;
}

.field-chain {
	display: flex;
	flex-wrap: wrap;
	align-items: center;
	font-size: 0.875rem;
	color: #374151;
	gap: 0.25rem;
}

.field-item {
	display: inline-flex;
	align-items: center;
	background-color: #f3f4f6;
	padding: 0.25rem 0.5rem;
	border-radius: 9999px;
	gap: 0.25rem;
}

.arrow {
	color: #9ca3af;
	margin: 0 0.25rem;
}

.combo-container {
	position: relative;
}

.combo-input {
	width: 100%;
	padding: 6px 8px;
	border: 1px solid #ccc;
	border-radius: 4px;
	font-size: 14px;
}

.combo-options {
	position: absolute;
	top: 100%;
	left: 0;
	width: 100%;
	background: white;
	border: 1px solid #e5e7eb;
	border-radius: 4px;
	box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
	z-index: 10;
}

.combo-option {
	padding: 8px 12px;
	display: flex;
	align-items: center;
	gap: 0.5rem;
	cursor: pointer;
}

.combo-option.active {
	background-color: #f9fafb;
}

.combo-option.selected {
	background-color: #eff6ff;
}

.empty-state {
	padding: 8px 12px;
	color: #6b7280;
	font-style: italic;
	text-align: center;
}
</style>
