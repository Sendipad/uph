<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { Combobox, ComboboxInput, ComboboxOptions, ComboboxOption } from "@headlessui/vue";
import { safeFrappeUtils } from "../utils";

const utils = safeFrappeUtils();

const props = defineProps({
	modelValue: {
		type: [Array, String],
		default: () => [],
	},
	rootDoctypes: {
		type: [Array, String],
		required: true,
	},
	getFields: Function,
	disabled: Boolean,
});

const emit = defineEmits(["update:modelValue"]);

const value = computed({
	get: () => {
		try {
			return Array.isArray(props.modelValue)
				? props.modelValue
				: JSON.parse(props.modelValue || "[]");
		} catch (e) {
			console.warn("DocFieldCrawl: Failed to parse modelValue", e);
			return [];
		}
	},
	set: (val) => {
		emit("update:modelValue", JSON.stringify(val));
	},
});

const search = ref("");
const selectedField = ref(null);
const fieldStack = ref([]);
const currentDoctypes = ref([]);
const availableFields = ref([]);

const isLoading = ref(false);
const loadError = ref(false);
const showOptions = ref(false);

const isOpen = ref(false); // control Combobox open state

const showInput = computed(() => {
	if (!fieldStack.value.length) return true;
	const lastFieldType = fieldStack.value[fieldStack.value.length - 1].fieldtype;
	return ["Link", "Table", "MultiSelectTable"].includes(lastFieldType);
});

function normalizeDoctypes(input) {
	if (!input) return [];
	const array = Array.isArray(input) ? input : [input];
	return array.filter((dt) => typeof dt === "string" && dt.trim().length > 0);
}

function getFieldIcon(fieldtype) {
	const map = {
		Data: "edit",
		Link: "link",
		Select: "arrow-down",
		Date: "calendar",
		Int: "hash",
		Check: "check-square",
		Currency: "dollar-sign",
		Float: "percent",
		Text: "align-left",
		Table: "table",
		MultiSelectTable: "table",
	};
	return map[fieldtype] || "circle";
}

function emitFieldPath() {
	value.value = [
		normalizeDoctypes(props.rootDoctypes),
		fieldStack.value.map((f) => ({
			fieldname: f.fieldname,
			fieldtype: f.fieldtype,
			options: f.options,
			label: f.label,
		})),
	];
}

async function loadFieldsForDoctypes(doctypes) {
	if (!props.getFields) return [];

	isLoading.value = true;
	loadError.value = false;
	try {
		const fields = await props.getFields(doctypes);
		return fields || [];
	} catch (e) {
		console.error("Failed to load fields:", e);
		loadError.value = true;
		return [];
	} finally {
		isLoading.value = false;
	}
}

async function initializeFromModel() {
	if (!Array.isArray(value.value) || value.value.length !== 2) return;

	const [doctypeList, path] = value.value || [];

	if (!Array.isArray(path)) return;

	currentDoctypes.value = normalizeDoctypes(doctypeList || props.rootDoctypes);

	let fields = await loadFieldsForDoctypes(currentDoctypes.value);

	for (const field of path) {
		const match = fields.find((f) => f.fieldname === field.fieldname);
		if (!match) break;
		fieldStack.value.push(match);

		if (["Link", "Table", "MultiSelectTable"].includes(match.fieldtype) && match.options) {
			currentDoctypes.value = [match.options];
			fields = await loadFieldsForDoctypes(match.options);
		} else {
			break;
		}
	}
	availableFields.value = fields;
}

const filteredFields = computed(() => {
	if (!search.value) return availableFields.value;
	const term = search.value.toLowerCase();
	return availableFields.value.filter((f) => (f.label || f.fieldname).toLowerCase().includes(term));
});

async function selectField(field) {
	if (props.disabled) return;

	fieldStack.value.push(field);
	selectedField.value = null;
	search.value = "";
	isOpen.value = false;

	if (["Link", "Table", "MultiSelectTable"].includes(field.fieldtype) && field.options) {
		currentDoctypes.value = [field.options];
		availableFields.value = (await loadFieldsForDoctypes(field.options)) || [];
	} else {
		availableFields.value = [];
	}

	emitFieldPath();
}

function removeLast() {
	if (props.disabled) return;

	fieldStack.value.pop();

	if (!fieldStack.value.length) {
		currentDoctypes.value = normalizeDoctypes(props.rootDoctypes);
		loadFieldsForDoctypes(currentDoctypes.value).then((fields) => {
			availableFields.value = fields;
			emitFieldPath();
		});
		return;
	}

	const lastField = fieldStack.value[fieldStack.value.length - 1];
	const targetDoctype = lastField.options || normalizeDoctypes(props.rootDoctypes)[0];

	currentDoctypes.value = [targetDoctype];
	loadFieldsForDoctypes(targetDoctype).then((fields) => {
		availableFields.value = fields;
		emitFieldPath();
	});
}

onMounted(async () => {
	await initializeFromModel();

	if (!fieldStack.value.length) {
		currentDoctypes.value = normalizeDoctypes(props.rootDoctypes);
		availableFields.value = (await loadFieldsForDoctypes(currentDoctypes.value)) || [];
	}
});

watch(
	() => props.rootDoctypes,
	async (newVal) => {
		if (!fieldStack.value.length && newVal?.length) {
			currentDoctypes.value = normalizeDoctypes(newVal);
			availableFields.value = (await loadFieldsForDoctypes(currentDoctypes.value)) || [];
		}
	},
	{ immediate: true, deep: true },
);

watch(fieldStack, () => {
	selectedField.value = null;
});
</script>

<template>
	<div class="doc-field-crawl">
		<div class="breadcrumb">
			<span v-for="(item, index) in fieldStack" :key="index">
				{{ item.label || item.fieldname }}
				<span v-if="index < fieldStack.length - 1"> › </span>
			</span>
			<button v-if="fieldStack.length" @click="removeLast" class="remove-btn">×</button>
		</div>

		<div v-if="isLoading" class="field-loading">
			<span class="spinner"></span> {{ __("Loading fields...") }}
		</div>

		<div v-else-if="loadError" class="field-error">
			<span v-html="utils.icon('warning', 'sm')"></span> {{ __("Error loading fields") }}
		</div>

		<Combobox
			v-if="showInput"
			v-model="selectedField"
			v-model:open="isOpen"
			@update:modelValue="selectField"
			:disabled="disabled"
			:as="Fragment"
			@focus="() => (isOpen.value = true)"
		>
			<div class="relative">
				<ComboboxInput
					class="combobox-input"
					:displayValue="(field) => field?.label || ''"
					@input="search = $event.target.value"
					:placeholder="__('Search field...')"
					@focus="isOpen = true"
				/>
				<ComboboxOptions v-if="isOpen" static class="combobox-options">
					<ComboboxOption
						v-for="field in filteredFields"
						:key="field.fieldname"
						:value="field"
						as="template"
						v-slot="{ active, selected, disabled }"
					>
						<div
							class="combobox-option"
							:class="{
								'option-active': active,
								'option-selected': selected,
								'option-disabled': disabled,
							}"
						>
							<span v-html="utils.icon(getFieldIcon(field.fieldtype), 'xs')"></span>
							<span>{{ field.label || field.fieldname }}</span>
							<span v-if="selected">✔</span>
						</div>
					</ComboboxOption>

					<div v-if="!filteredFields.length" class="empty-state">
						{{ __("No matching fields") }}
					</div>
				</ComboboxOptions>
			</div>
		</Combobox>
	</div>
</template>

<style scoped>
.relative {
	position: relative;
}

.doc-field-crawl {
	position: relative; /* ensure root wrapper is relative */

	border: 1px solid #ccc;
	padding: 12px;
	border-radius: 6px;
	max-width: 450px;
	background: #fff;
}
.breadcrumb {
	font-size: 14px;
	margin-bottom: 8px;
	color: #444;
	display: flex;
	align-items: center;
	flex-wrap: wrap;
}
.remove-btn {
	margin-left: 8px;
	background: transparent;
	border: none;
	color: #c00;
	font-weight: bold;
	font-size: 16px;
	cursor: pointer;
}
.field-loading {
	display: flex;
	align-items: center;
	gap: 8px;
	color: #6b7280;
	background-color: #f3f4f6;
	padding: 8px;
	border-radius: 4px;
	margin-bottom: 8px;
}
.field-error {
	display: flex;
	align-items: center;
	gap: 8px;
	color: #b91c1c;
	background: #fef2f2;
	padding: 8px;
	border-radius: 4px;
	margin-bottom: 8px;
}
.spinner {
	display: inline-block;
	width: 12px;
	height: 12px;
	border: 2px solid rgba(0, 0, 0, 0.1);
	border-radius: 50%;
	border-top-color: #3b82f6;
	animation: spin 1s linear infinite;
}
@keyframes spin {
	to {
		transform: rotate(360deg);
	}
}
.combobox-input {
	width: 100%;
	padding: 8px 12px;
	border-radius: 6px;
	border: 1px solid #d1d5db;
	background: white;
	font-size: 0.9rem;
}
.combobox-options {
	position: absolute;
	z-index: 50;
	top: 100%;
	left: 0;
	width: 100%;
	box-sizing: border-box;
	background: white;
	border: 1px solid #d1d5db;
	border-radius: 4px;
	margin-top: 4px;
	max-height: 240px;
	overflow-y: auto;
	list-style: none;
	padding: 0;
	box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
	font-size: 0.9rem;
}
.combobox-option {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 8px;
	padding: 8px 12px;
	cursor: pointer;
	transition: background-color 0.15s ease;
	border-bottom: 1px solid #f3f4f6;
}
.combobox-option:last-child {
	border-bottom: none;
}
.option-active {
	background-color: #f3f4f6;
}
.option-selected {
	font-weight: 600;
}
.option-disabled {
	color: #9ca3af;
	cursor: not-allowed;
	opacity: 0.6;
}
.empty-state {
	padding: 8px 12px;
	color: #6b7280;
	font-style: italic;
	text-align: center;
}
</style>
