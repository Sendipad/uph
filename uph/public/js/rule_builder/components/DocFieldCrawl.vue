<script setup>
import { ref, computed, onMounted, watch, nextTick, onBeforeUnmount } from "vue";
import { Combobox, ComboboxInput, ComboboxOptions, ComboboxOption } from "@headlessui/vue";
import { safeFrappeUtils } from "../utils";
import Breadcrumb from "./Breadcrumb.vue";

const utils = safeFrappeUtils();

const props = defineProps({
	modelValue: { type: [Array, String], default: () => [] },
	rootDoctypes: { type: [Array, String], required: true },
	getFields: Function,
	disabled: Boolean,
	placeholder: { type: String, default: "Select field..." },
});

const emit = defineEmits(["update:modelValue", "field-change"]);

const search = ref("");
const selectedField = ref(null);
const fieldStack = ref([]);
const currentDoctypes = ref([]);
const availableFields = ref([]);

const isLoading = ref(false);
const loadError = ref(false);
const isOpen = ref(false);

const rootRef = ref(null);
const inputRef = ref(null);
const lastSelectedField = ref(null);

const dropdownStyle = ref({
	position: "absolute",
	top: "0px",
	left: "0px",
	width: "auto",
	minWidth: "200px",
	zIndex: 1000,
});

function normalizeDoctypes(input) {
	return Array.isArray(input) ? input : [input];
}

async function loadFieldsForDoctypes(doctypes) {
	if (!props.getFields) return [];
	isLoading.value = true;
	loadError.value = false;
	try {
		return (await props.getFields(doctypes)) || [];
	} catch (e) {
		loadError.value = true;
		return [];
	} finally {
		isLoading.value = false;
	}
}

function emitFieldPath() {
	// Emit modelValue as JSON string: [rootDoctypes, fieldStack array]
	emit(
		"update:modelValue",
		JSON.stringify([
			normalizeDoctypes(props.rootDoctypes),
			fieldStack.value.map(({ fieldname, fieldtype, options, label }) => ({
				fieldname,
				fieldtype,
				options,
				label,
			})),
		]),
	);
}

const value = computed({
	get() {
		try {
			return Array.isArray(props.modelValue)
				? props.modelValue
				: JSON.parse(props.modelValue || "[]");
		} catch {
			return [];
		}
	},
	set(val) {
		emit("update:modelValue", JSON.stringify(val));
	},
});

const filteredFields = computed(() => {
	if (!search.value) return availableFields.value;
	const term = search.value.toLowerCase();
	return availableFields.value.filter((f) => (f.label || f.fieldname).toLowerCase().includes(term));
});

const showInput = computed(() => {
	if (props.disabled) return false;

	// If no fields selected, always show input
	if (!fieldStack.value.length) return true;

	// Get the last selected field
	const lastField = fieldStack.value.at(-1);

	// Only show input if last field is one of these types
	return ["Link", "Table", "MultiSelectTable"].includes(lastField?.fieldtype);
});

function handleBreadcrumbClick(index) {
	// When clicking a breadcrumb item, truncate the stack to that point
	if (index < fieldStack.value.length - 1) {
		removeField(index + 1);
	}
}
function isSameField(a, b) {
	if (!a || !b) return false;
	return a.fieldname === b.fieldname && a.fieldtype === b.fieldtype;
}
async function handleSelect(field) {
	if (props.disabled || !field || isSameField(field, lastSelectedField.value)) return;

	// Only proceed if this is a new selection
	if (!isSameField(field, fieldStack.value.at(-1))) {
		await selectField(field);
		lastSelectedField.value = field;
	}

	await nextTick();
	selectedField.value = null;
	search.value = "";
}

async function selectField(field) {
	if (!field) return;

	const oldVal = [...fieldStack.value];
	fieldStack.value.push(field);
	search.value = "";
	isOpen.value = false;

	if (["Link", "Table", "MultiSelectTable"].includes(field.fieldtype) && field.options) {
		currentDoctypes.value = [field.options];
		availableFields.value = (await loadFieldsForDoctypes(currentDoctypes.value)) || [];
	} else {
		currentDoctypes.value = [];
		availableFields.value = [];
	}

	emitFieldPath();

	emit("field-change", {
		field: "field_chain",
		oldVal,
		newVal: [...fieldStack.value],
	});
}

function removeField(index) {
	if (props.disabled) return;

	const oldVal = [...fieldStack.value];
	// Remove from index to end, truncating the stack
	fieldStack.value.splice(index);
	lastSelectedField.value = null; // 👈 reset last selection

	// Update currentDoctypes based on new last field or rootDoctypes
	if (fieldStack.value.length) {
		const last = fieldStack.value.at(-1);
		currentDoctypes.value = last?.options ? [last.options] : normalizeDoctypes(props.rootDoctypes);
	} else {
		currentDoctypes.value = normalizeDoctypes(props.rootDoctypes);
	}

	loadFieldsForDoctypes(currentDoctypes.value).then((fields) => {
		availableFields.value = fields;
		emitFieldPath();
		emit("field-change", { field: "field_chain", oldVal, newVal: [...fieldStack.value] });
	});
}

function startEditing() {
	if (props.disabled || !showInput.value) return;
	isOpen.value = true;
	nextTick(() => {
		inputRef.value?.focus();
		updateDropdownPosition();
	});
}

function updateDropdownPosition() {
	const rootEl = rootRef.value;
	if (!rootEl) return;

	const rect = rootEl.getBoundingClientRect();

	dropdownStyle.value = {
		position: "absolute",
		top: `${rect.bottom + window.scrollY + 4}px`,
		left: `${rect.left + window.scrollX}px`,
		width: `${rect.width}px`,
		minWidth: "200px",
		zIndex: 1000,
	};
}

function handleFocusIn(e) {
	if (!rootRef.value?.contains(e.target)) {
		isOpen.value = false;
	}
}

function onScrollOrResize() {
	if (isOpen.value) updateDropdownPosition();
}

onMounted(async () => {
	const [doctypes, path] = value.value;
	currentDoctypes.value = normalizeDoctypes(doctypes || props.rootDoctypes);
	let fields = await loadFieldsForDoctypes(currentDoctypes.value);

	for (const savedField of path || []) {
		// Try to match saved field with loaded fields by fieldname & fieldtype (better match)
		const match = fields.find(
			(f) => f.fieldname === savedField.fieldname && f.fieldtype === savedField.fieldtype,
		);
		if (!match) break;

		fieldStack.value.push(match);

		if (["Link", "Table", "MultiSelectTable"].includes(match.fieldtype) && match.options) {
			currentDoctypes.value = [match.options];
			fields = await loadFieldsForDoctypes(currentDoctypes.value);
		} else {
			break;
		}
	}
	availableFields.value = fields;

	document.addEventListener("focusin", handleFocusIn);
	window.addEventListener("scroll", onScrollOrResize, true);
	window.addEventListener("resize", onScrollOrResize);
});

onBeforeUnmount(() => {
	document.removeEventListener("focusin", handleFocusIn);
	window.removeEventListener("scroll", onScrollOrResize, true);
	window.removeEventListener("resize", onScrollOrResize);
});

// Watch for rootDoctypes changes
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
</script>

<template>
	<div ref="rootRef" class="compact-field-crawl">
		<!-- Breadcrumb display (always visible when there are items) -->
		<Breadcrumb
			v-if="fieldStack.length"
			:items="fieldStack"
			:clickable="!disabled"
			:show-remove="!disabled ? 'last' : 'none'"
			:separator="'›'"
			@item-click="handleBreadcrumbClick"
			@remove="removeField(fieldStack.length - 1)"
			class="breadcrumb-preview"
		>
			<template #item="{ item }">
				{{ item.label || item.fieldname }}
			</template>
		</Breadcrumb>

		<!-- Combobox input (only shown when needed) -->
		<Combobox
			v-if="showInput"
			:disabled="disabled"
			v-model="selectedField"
			v-model:open="isOpen"
			@update:modelValue="handleSelect"
		>
			<div class="combobox-container">
				<div class="input-wrapper" @click="startEditing">
					<ComboboxInput
						ref="inputRef"
						class="combobox-input"
						:modelValue="search"
						@update:modelValue="(val) => (search = val)"
						:placeholder="fieldStack.length ? 'Add next field...' : placeholder"
						@focus="isOpen = true"
						autocomplete="off"
						spellcheck="false"
					/>
				</div>

				<ComboboxOptions v-show="isOpen" as="div" static class="combobox-options">
					<ComboboxOption
						v-for="field in filteredFields"
						:key="field.fieldname + field.fieldtype"
						:value="field"
						v-slot="{ active }"
						as="template"
					>
						<div :class="['option', { active }]">
							{{ field.label || field.fieldname }}
							<span
								v-if="['Link', 'Table', 'MultiSelectTable'].includes(field.fieldtype)"
								class="type-indicator"
							>
								→
							</span>
						</div>
					</ComboboxOption>

					<div v-if="isLoading" class="empty-state">Loading fields...</div>
					<div v-else-if="loadError" class="empty-state error">Error loading fields</div>
					<div v-else-if="filteredFields.length === 0" class="empty-state">No fields found</div>
				</ComboboxOptions>
			</div>
		</Combobox>
	</div>
</template>

<style scoped>
.compact-field-crawl {
	display: flex;
	flex-direction: column;
	gap: 4px;
	width: 100%;
	position: relative;
}

.breadcrumb-preview {
	border: 1px solid #e2e8f0;
	border-radius: 6px;
	padding: 8px 12px;
	background-color: white;
}

.combobox-container {
	position: relative;
	width: 100%;
}

.input-wrapper {
	display: flex;
	align-items: center;
	padding: 8px 12px;
	border: 1px solid #e2e8f0;
	border-radius: 6px;
	min-height: 40px;
	background-color: white;
	cursor: text;
	width: 100%;
	box-sizing: border-box;
}

.combobox-input {
	flex: 1;
	min-width: 120px;
	border: none;
	outline: none;
	padding: 2px 0;
	font-size: 0.875rem;
	background: transparent;
}

.combobox-options {
	position: absolute;
	top: calc(100% + 4px);
	left: 0;
	width: 100%;
	max-height: 300px;
	overflow-y: auto;
	background-color: white;
	border: 1px solid #e2e8f0;
	border-radius: 6px;
	box-shadow:
		0 4px 6px -1px rgba(0, 0, 0, 0.1),
		0 2px 4px -1px rgba(0, 0, 0, 0.06);
	z-index: 50;
	margin-top: 2px;
}

.option {
	padding: 10px 12px;
	cursor: pointer;
	font-size: 0.875rem;
	display: flex;
	justify-content: space-between;
	align-items: center;
	transition: background-color 0.15s ease;
}

.option:hover,
.option.active {
	background-color: #f3f4f6;
}

.type-indicator {
	color: #9ca3af;
	font-weight: bold;
	margin-left: 8px;
}

.empty-state {
	padding: 10px 12px;
	color: #6b7280;
	font-size: 0.875rem;
	font-style: italic;
}

.empty-state.error {
	color: #ef4444;
}
</style>
