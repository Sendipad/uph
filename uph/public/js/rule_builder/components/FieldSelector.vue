<template>
  <div class="field-selector">
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

    <!-- Combobox UI -->
    <Combobox
      v-else
      :modelValue="selectedOption"
      @update:modelValue="onSelect"
      :disabled="disabled"
    >
      <div class="relative">
        <ComboboxInput
          class="combobox-input"
          :placeholder="placeholder"
          :displayValue="(item) => item?.label || ''"
          @input="query = $event.target.value"
          @focus="showOptions = true"
          @blur="handleBlur"
        />

        <!-- Always show options when focused -->
        <ComboboxOptions v-show="showOptions" static class="combobox-options">
          <ComboboxOption
            v-for="field in filteredFields"
            :key="field.value"
            :value="field"
            :disabled="field.disabled"
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
              <span
                v-html="utils.icon(getFieldIcon(field.fieldtype), 'xs')"
              ></span>
              <span>{{ field.label || field.value }}</span>
              <span v-if="selected">✔</span>
            </div>
          </ComboboxOption>

          <!-- Empty state -->
          <div v-if="!filteredFields.length" class="empty-state">
            {{ __("No matching fields found") }}
          </div>
        </ComboboxOptions>
      </div>
    </Combobox>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from "vue";
import {
  Combobox,
  ComboboxInput,
  ComboboxOptions,
  ComboboxOption,
} from "@headlessui/vue";
import { loadFieldOptions, getCachedFieldsForDoctype } from "../utils.js";
import { safeFrappeUtils } from "../utils";

const utils = safeFrappeUtils();

const props = defineProps({
  modelValue: String,
  documentType: [String, Array],
  placeholder: { type: String, default: "Select Field" },
  disabled: Boolean,
});

const emit = defineEmits(["update:modelValue", "change"]);

const isLoading = ref(false);
const loadError = ref(false);
const fieldOptions = ref([]);
const selectedOption = ref(null);
const query = ref("");
const showOptions = ref(false); // Control options visibility

// Always show options when component mounts with value
onMounted(() => {
  if (!props.modelValue) {
    showOptions.value = true;
  }
  if (props.documentType) {
    loadOptions();
  }
});

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
  };
  return map[fieldtype] || "circle";
}

// Optimized field loading
async function loadOptions() {
  if (!props.documentType) return;

  isLoading.value = true;
  loadError.value = false;

  try {
    const normalizedTypes = Array.isArray(props.documentType)
      ? [...new Set(props.documentType)].sort()
      : [props.documentType];

    // Load fields without filtering by query
    const fields = await loadFieldOptions(normalizedTypes);

    // Create a map for faster lookups
    const fieldMap = new Map();
    fields.forEach((field) => fieldMap.set(field.value, field));

    fieldOptions.value = fields;
    updateSelectedOption();
  } catch (e) {
    console.error("Field load failed:", e);
    loadError.value = true;
    fieldOptions.value = [];
  } finally {
    isLoading.value = false;
  }
}

// Update selected option when value changes
function updateSelectedOption() {
  selectedOption.value =
    fieldOptions.value.find((f) => f.value === props.modelValue) || null;
}

watch(() => props.documentType, loadOptions);

watch(() => props.modelValue, updateSelectedOption);

// Emits value on select
function onSelect(option) {
  selectedOption.value = option;
  emit("update:modelValue", option?.value || "");
  emit("change", option?.value || "");
}

// Filtered options (optimized)
const filteredFields = computed(() => {
  if (!query.value) return fieldOptions.value;

  const term = query.value.toLowerCase();
  return fieldOptions.value.filter((f) =>
    (f.label || f.value).toLowerCase().includes(term)
  );
});

// Handle blur with delay to allow selection
function handleBlur() {
  setTimeout(() => {
    showOptions.value = false;
  }, 200);
}
</script>

<style scoped>
.relative {
  position: relative;
}
.field-selector {
  min-width: 180px;
  flex: 1;
}
.field-loading,
.field-error {
  padding: 8px;
  border-radius: 4px;
  margin-bottom: 5px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.field-loading {
  background-color: #f3f4f6;
}

.field-error {
  background-color: #fef2f2;
  color: #b91c1c;
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

option:disabled {
  color: #9ca3af;
  font-style: italic;
}
.field-loading,
.field-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  font-size: 0.9rem;
  border-radius: 4px;
}

.field-loading {
  color: #6b7280;
}

.field-error {
  color: #b91c1c;
  background: #fef2f2;
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

select {
  width: 100%;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  background: white;
  font-size: 0.9rem;
}

select:disabled {
  background-color: #f3f4f6;
  cursor: not-allowed;
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
  z-index: 10;
  top: 100%;
  left: 0;
  width: 100%; /* ✅ Match input */
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
  justify-content: space-between; /* icon-label on left, checkmark on right */
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
.combobox-options {
  /* ... existing styles ... */
  z-index: 50; /* Ensure it's above other elements */
}

.empty-state {
  padding: 8px 12px;
  color: #6b7280;
  font-style: italic;
  text-align: center;
}

.combobox-option {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
