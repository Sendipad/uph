<script setup>
// Imports
import { ref, computed, onMounted, watch, nextTick, onBeforeUnmount } from "vue";
import { Combobox, ComboboxInput, ComboboxOptions, Portal } from "@headlessui/vue";
import { safeFrappeUtils } from "../utils";
import Breadcrumb from "./Breadcrumb.vue";

// Utilities
const utils = safeFrappeUtils();

// Props and Emits
const props = defineProps({
	modelValue: { type: [Array, String], default: () => [] },
	rootDoctypes: { type: [Array, String], required: true },
	getFields: Function,
	disabled: Boolean,
	placeholder: { type: String, default: "Select field..." },
});
const emit = defineEmits(["update:modelValue", "field-change"]);

// State
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
const highlightedIndex = ref(0);

// Dropdown positioning
const dropdownStyle = ref({
	position: "absolute",
	top: "0px",
	left: "0px",
	width: "auto",
	minWidth: "200px",
	zIndex: 1000,
});

// Helpers
const normalizeDoctypes = (input) => (Array.isArray(input) ? input : [input]);

async function loadFieldsForDoctypes(doctypes) {
	if (!props.getFields) return [];
	isLoading.value = true;
	loadError.value = false;
	try {
		return (await props.getFields(doctypes)) || [];
	} catch {
		loadError.value = true;
		return [];
	} finally {
		isLoading.value = false;
	}
}

function emitFieldPath() {
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

// Computed values
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
	const term = search.value.trim().toLowerCase();
	if (!term) return availableFields.value;
	return availableFields.value.filter((field) => {
		const label = (field.label || field.fieldname || "").toLowerCase();
		const options = typeof field.options === "string" ? field.options.toLowerCase() : "";
		return label.includes(term) || options.includes(term);
	});
});

const showInput = computed(() => {
	if (props.disabled) return false;
	if (!fieldStack.value.length) return true;
	return ["Link", "Table", "MultiSelectTable"].includes(fieldStack.value.at(-1)?.fieldtype);
});

const isSameField = (a, b) =>
	!!a && !!b && a.fieldname === b.fieldname && a.fieldtype === b.fieldtype;

function moveHighlight(delta) {
	const count = filteredFields.value.length;
	if (count === 0) return;
	highlightedIndex.value = (highlightedIndex.value + delta + count) % count;
}

function selectHighlighted() {
	const field = filteredFields.value[highlightedIndex.value];
	if (field) handleSelect(field);
}

async function handleSelect(field) {
	if (props.disabled || !field) return;

	// Optional: Debugging log
	// console.log("Selected:", field);

	const alreadySelected =
		isSameField(field, lastSelectedField.value) || isSameField(field, fieldStack.value.at(-1));

	if (!alreadySelected) {
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

	const { fieldtype, options } = field;

	if (["Link", "Table", "MultiSelectTable"].includes(fieldtype) && options) {
		currentDoctypes.value = [options];
		availableFields.value = await loadFieldsForDoctypes(currentDoctypes.value);
	} else {
		currentDoctypes.value = [];
		availableFields.value = [];
	}

	emitFieldPath();
	emit("field-change", { field: "field_chain", oldVal, newVal: [...fieldStack.value] });
}

function removeField(index) {
	if (props.disabled) return;

	const oldVal = [...fieldStack.value];
	fieldStack.value.splice(index);
	lastSelectedField.value = null;

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

function handleBreadcrumbClick(index) {
	if (index < fieldStack.value.length - 1) {
		removeField(index + 1);
	}
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
	Object.assign(dropdownStyle.value, {
		top: `${rect.bottom + window.scrollY + 4}px`,
		left: `${rect.left + window.scrollX}px`,
		width: `${rect.width}px`,
	});
}

function handleFocusIn(e) {
	if (!rootRef.value?.contains(e.target)) {
		isOpen.value = false;
	}
}

function onScrollOrResize() {
	if (isOpen.value) updateDropdownPosition();
}

// Lifecycle
onMounted(async () => {
	const [doctypes, path] = value.value;
	currentDoctypes.value = normalizeDoctypes(doctypes || props.rootDoctypes);
	let fields = await loadFieldsForDoctypes(currentDoctypes.value);

	for (const savedField of path || []) {
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

// Watchers
watch(
	() => props.rootDoctypes,
	async (newVal) => {
		if (!fieldStack.value.length && newVal?.length) {
			currentDoctypes.value = normalizeDoctypes(newVal);
			availableFields.value = await loadFieldsForDoctypes(currentDoctypes.value);
		}
	},
	{ immediate: true, deep: true },
);

watch(isOpen, async (val) => {
	if (val) {
		await nextTick();
		updateDropdownPosition();
	}
});
watch(
	() => props.modelValue,
	async (newVal) => {
		try {
			const [doctypes, path] = Array.isArray(newVal) ? newVal : JSON.parse(newVal || "[]");

			currentDoctypes.value = normalizeDoctypes(doctypes || props.rootDoctypes);
			let fields = await loadFieldsForDoctypes(currentDoctypes.value);

			fieldStack.value = [];
			for (const savedField of path || []) {
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
		} catch (e) {
			console.error("Failed to sync from modelValue:", e);
		}
	},
	{ deep: true },
);
</script>
<template>
	<div ref="rootRef" class="compact-field-crawl" :dir="direction">
		<!-- Only show inline combined input+breadcrumb if input allowed -->
		<Combobox
			v-if="showInput"
			:disabled="disabled"
			v-model="selectedField"
			v-model:open="isOpen"
			@update:modelValue="handleSelect"
		>
			<div class="combobox-container">
				<!-- Breadcrumb + Input in same row -->
				<div class="breadcrumb-input-wrapper">
					<!-- Breadcrumb (scrollable) -->
					<Breadcrumb
						v-if="fieldStack.length"
						:items="fieldStack"
						:clickable="!disabled"
						:show-remove="!disabled ? 'last' : 'none'"
						:separator="separator"
						@item-click="handleBreadcrumbClick"
						@remove="removeField(fieldStack.length - 1)"
						class="breadcrumb-inline"
					>
						<template #item="{ item }">
							{{ item.label || item.fieldname }}
						</template>
					</Breadcrumb>

					<!-- Input after breadcrumb -->
					<ComboboxInput
						ref="inputRef"
						class="combobox-input"
						:value="search"
						@input="search = $event.target.value"
						:placeholder="fieldStack.length ? 'Add next field…' : placeholder"
						@focus="isOpen = true"
						@keydown.down.prevent="moveHighlight(1)"
						@keydown.up.prevent="moveHighlight(-1)"
						@keydown.enter.prevent="selectHighlighted"
					/>
				</div>

				<!-- Dropdown Options -->
				<Portal v-if="isOpen">
					<div :style="dropdownStyle" class="combobox-portal-wrapper">
						<ComboboxOptions as="div" static class="combobox-options">
							<div
								v-for="(field, i) in filteredFields"
								:key="field.fieldname + field.fieldtype"
								class="option"
								:class="{ active: i === highlightedIndex }"
								@click="handleSelect(field)"
							>
								{{ field.label || field.fieldname }}
								<span
									v-if="['Link', 'Table', 'MultiSelectTable'].includes(field.fieldtype)"
									class="type-indicator"
								>
									{{ direction === "rtl" ? "←" : "→" }}
								</span>
							</div>

							<div v-if="isLoading" class="empty-state">Loading fields...</div>
							<div v-else-if="loadError" class="empty-state error">Error loading fields</div>
							<div v-else-if="filteredFields.length === 0" class="empty-state">No fields found</div>
						</ComboboxOptions>
					</div>
				</Portal>
			</div>
		</Combobox>

		<!-- Fallback: only breadcrumb if input is disabled -->
		<Breadcrumb
			v-else-if="fieldStack.length"
			:items="fieldStack"
			:clickable="!disabled"
			:show-remove="!disabled ? 'last' : 'none'"
			:separator="separator"
			@item-click="handleBreadcrumbClick"
			@remove="removeField(fieldStack.length - 1)"
			class="breadcrumb-preview"
		>
			<template #item="{ item }">
				{{ item.label || item.fieldname }}
			</template>
		</Breadcrumb>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";

// Add direction detection
const direction = computed(() => {
	return document.documentElement.dir === "rtl" ? "rtl" : "ltr";
});

// Update separator based on direction
const separator = computed(() => {
	return direction.value === "rtl" ? "‹" : "›";
});
</script>

<style scoped>
.compact-field-crawl {
	display: flex;
	flex-direction: column;
	gap: 4px;
	width: 100%;
	position: relative;
}

/* Breadcrumb + Input wrapper */
.breadcrumb-input-wrapper {
	display: flex;
	align-items: center;
	overflow-x: auto;
	white-space: nowrap;
	border: 1px solid #e2e8f0;
	border-radius: 6px;
	padding: 6px 8px;
	background-color: white;
	flex-direction: row;
}

[dir="rtl"] .breadcrumb-input-wrapper {
	flex-direction: row-reverse;
}

.breadcrumb-inline {
	display: inline-flex;
	white-space: nowrap;
	flex-shrink: 0;
}

.combobox-input {
	flex: 1 0 auto;
	min-width: 100px;
	border: none;
	outline: none;
	background: transparent;
	padding: 0 6px;
	font-size: 0.875rem;
}

[dir="rtl"] .combobox-input {
	padding-right: 6px;
	padding-left: 0;
}

/* Breadcrumb preview style */
.breadcrumb-preview {
	border: 1px solid #e2e8f0;
	border-radius: 6px;
	padding: 8px 12px;
	background-color: white;
}

/* Combobox dropdown styles */
.combobox-container {
	position: relative;
	width: 100%;
}

.combobox-options {
	position: absolute;
	top: calc(100% + 4px);
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

[dir="ltr"] .combobox-options {
	left: 0;
	right: auto;
}

[dir="rtl"] .combobox-options {
	right: 0;
	left: auto;
}

/* Option styles */
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

[dir="rtl"] .type-indicator {
	margin-left: 0;
	margin-right: 8px;
}

/* Empty state styles */
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
