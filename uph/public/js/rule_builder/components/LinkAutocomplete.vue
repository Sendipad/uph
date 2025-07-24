<template>
	<div class="combobox-wrapper">
		<!-- Multiselect tags -->
		<div v-if="multiple && selected.length" class="selected-tags">
			<span v-for="item in selected" :key="item.value" class="tag">
				{{ item.label }}
				<button @click.stop="removeTag(item)" class="remove-tag">
					<span v-html="frappe.utils.icon('delete', 'xs')"></span>
				</button>
			</span>
		</div>

		<!-- Combobox with optimized UX -->
		<Combobox v-model="selected" :multiple="multiple">
			<div class="relative">
				<ComboboxInput
					class="combobox-input"
					:displayValue="getDisplayValue"
					@change="query = $event.target.value"
					@focus="showOptions = true"
					@blur="handleBlur"
					:placeholder="placeholder"
				/>

				<!-- Loading indicator -->
				<span v-if="isLoading" class="absolute right-8 top-2.5">
					<span class="mini-spinner"></span>
				</span>

				<!-- Clear button -->
				<button
					v-if="!multiple && selected"
					@click="clearSelection"
					type="button"
					class="clear-btn"
				>
					✕
				</button>

				<!-- Options dropdown -->
				<ComboboxOptions v-show="showOptions" static class="combobox-options">
					<!-- Empty state -->
					<div v-if="!options.length && !isLoading" class="empty-state">
						{{ __("No options found") }}
					</div>

					<ComboboxOption
						v-for="option in options"
						:key="option.value"
						:value="option"
						v-slot="{ active, selected: isSelected }"
						as="div"
					>
						<div
							class="combobox-option"
							:class="{
								'option-active': active,
								'option-selected': isSelected,
							}"
						>
							<span>{{ option.label }}</span>
							<span v-if="isSelected">✔</span>
						</div>
					</ComboboxOption>
				</ComboboxOptions>
			</div>
		</Combobox>
	</div>
</template>

<script setup>
import { ref, watch } from "vue";
import { Combobox, ComboboxInput, ComboboxOptions, ComboboxOption } from "@headlessui/vue";
import { useDebounceFn } from "@vueuse/core";

const props = defineProps({
	modelValue: [Object, Array, String],
	doctype: String,
	placeholder: { type: String, default: "Search..." },
	multiple: { type: Boolean, default: false },
});

const emit = defineEmits(["update:modelValue"]);

// Reactive state
const query = ref("");
const options = ref([]);
const selected = ref(props.multiple ? [] : null);
const showOptions = ref(false);
const isLoading = ref(false);
const debouncedSearch = useDebounceFn(searchOptions, 300);

// Initialize with current value
watch(() => props.modelValue, initSelected, { immediate: true });

// Handle external value changes
function initSelected(val) {
	if (!val) {
		selected.value = props.multiple ? [] : null;
		return;
	}

	if (props.multiple) {
		selected.value = (val || []).map((v) => ({ value: v, label: v }));
	} else {
		selected.value = { value: val, label: val };
	}
}

// Get display value for input
function getDisplayValue() {
	if (props.multiple) return "";
	return selected.value?.label || "";
}

// Handle selection changes
watch(selected, (newVal) => {
	if (props.multiple) {
		emit(
			"update:modelValue",
			newVal.map((item) => item.value),
		);
	} else {
		emit("update:modelValue", newVal?.value || "");
	}
});

// Search with debounce
watch(query, () => {
	if (!props.doctype) return;
	isLoading.value = true;
	debouncedSearch();
});

async function searchOptions() {
	try {
		const res = await frappe.call("frappe.desk.search.search_link", {
			doctype: props.doctype,
			txt: query.value,
			page_length: 20,
		});

		options.value = (res.message?.results || res.message || []).map((r) => ({
			label: __(r.value),
			value: r.value,
		}));
	} catch (e) {
		console.error("Search failed:", e);
		options.value = [];
	} finally {
		isLoading.value = false;
	}
}

function removeTag(item) {
	selected.value = selected.value.filter((i) => i.value !== item.value);
}

function clearSelection() {
	selected.value = null;
	query.value = "";
	emit("update:modelValue", "");
}

// Handle blur with delay
function handleBlur() {
	setTimeout(() => {
		showOptions.value = false;
	}, 200);
}
</script>

<style scoped>
.combobox-wrapper {
	position: relative;
	width: 100%;
}

.selected-tags {
	display: flex;
	flex-wrap: wrap;
	gap: 6px;
	margin-bottom: 6px;
}

.tag {
	background: #f3f4f6;
	padding: 0.2rem 0.5rem;
	border-radius: 4px;
	border: 1px solid #d1d5db;
	display: flex;
	align-items: center;
	gap: 0.25rem;
	font-size: 0.85rem;
}

.remove-tag {
	background: none;
	border: none;
	color: #dc2626;
	font-size: 0.75rem;
	cursor: pointer;
	display: flex;
	align-items: center;
}

.combobox-input {
	width: 100%;
	padding: 0.5rem 2rem 0.5rem 0.75rem;
	border: 1px solid #d1d5db;
	border-radius: 4px;
	background: white;
	font-size: 0.9rem;
}

.clear-btn {
	position: absolute;
	top: 50%;
	right: 8px;
	transform: translateY(-50%);
	background: none;
	border: none;
	font-size: 1rem;
	color: #9ca3af;
	cursor: pointer;
	width: 24px;
	height: 24px;
	display: flex;
	align-items: center;
	justify-content: center;
}

.clear-btn:hover {
	color: #6b7280;
}

.combobox-options {
	position: absolute;
	z-index: 50;
	background: white;
	border: 1px solid #d1d5db;
	border-radius: 4px;
	width: 100%;
	margin-top: 0.25rem;
	max-height: 300px;
	overflow-y: auto;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.combobox-option {
	padding: 0.5rem 0.75rem;
	cursor: pointer;
	display: flex;
	justify-content: space-between;
}

.combobox-option:hover {
	background-color: #f3f4f6;
}

.option-selected {
	background-color: #e0f2fe;
	font-weight: 500;
}

.empty-state {
	padding: 0.75rem;
	text-align: center;
	color: #6b7280;
	font-style: italic;
}

.mini-spinner {
	display: inline-block;
	width: 16px;
	height: 16px;
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
</style>
