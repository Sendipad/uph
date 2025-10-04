<template>
	<div v-if="flattenedColumns?.length" class="nested-grid-container">
		<!-- Main Grid -->
		<div
			class="nested-editable-grid"
			ref="gridRef"
			tabindex="0"
			@keydown="onKeydown"
			role="treegrid"
			:aria-rowcount="totalRowCount"
			:aria-colcount="flattenedColumns.length"
		>
			<!-- Column Headers -->
			<div class="grid-header" role="row" aria-rowindex="1">
				<div
					v-for="(col, colIndex) in flattenedColumns"
					:key="col.fieldname || col.label"
					class="grid-header-cell"
					:style="{ width: getColumnWidth(col) }"
					role="columnheader"
					:aria-colindex="colIndex + 1"
				>
					<div class="header-content">
						<span v-if="col.fieldname === groupingKeyField" class="group-indicator"></span>
						{{ col.label }}
						<span v-if="col.mandatory" class="mandatory-star" title="Mandatory">*</span>
					</div>
					<div
						class="resize-handle"
						@mousedown.prevent="initResize($event, col)"
						title="Resize column"
					/>
				</div>
			</div>

			<!-- Tree Rows -->
			<div
				class="grid-body"
				@scroll="handleScroll"
				ref="gridBodyRef"
				:style="{ height: `${totalRowCount * rowHeight}px` }"
				role="rowgroup"
			>
				<div
					class="grid-body-content"
					:style="{ transform: `translateY(${visibleRowStart * rowHeight}px)` }"
				>
					<div
						class="grid-cell indent-cell"
						:style="{ width: `${indentSize}px`, paddingLeft: `${getDepth(row) * indentSize}px` }"
						aria-hidden="true"
					></div>
					<template v-for="(row, rowIndex) in visibleRows" :key="getRowKey(row)">
						<div
							v-if="isGroupRow(row)"
							class="grid-row group-row"
							:class="{
								'is-group': true,
								expanded: isGroupExpanded(row),
								'is-focused': isRowFocused(visibleRowStart + rowIndex),
								'has-children': hasChildren(row),
								'is-dragging': draggedRow?.id === row.id,
							}"
							:style="{ paddingLeft: `${getDepth(row) * indentSize}px` }"
							role="row"
							:aria-level="getDepth(row) + 1"
							:aria-expanded="isGroupExpanded(row)"
							:aria-rowindex="getAriaRowIndex(rowIndex)"
							draggable="true"
							@dragstart="onDragStart($event, row)"
							@dragover.prevent="onDragOver($event, row)"
							@drop="onDrop($event, row)"
							@dragend="onDragEnd"
							@mouseenter="hoveredRow = visibleRowStart + rowIndex"
							@mouseleave="hoveredRow = null"
						>
							<!-- Selection Checkbox -->
							<div
								class="grid-cell selection-cell"
								v-if="showSelection"
								:style="{ width: getColumnWidth({ fieldname: 'selection' }) }"
							>
								<slot name="selection-cell" :row="row">
									<!-- Fallback checkbox -->
									<input
										type="checkbox"
										:checked="isRowSelected(row)"
										@change="toggleRowSelection(row)"
										@click.stop
									/>
								</slot>
							</div>

							<!-- Drag Handle -->
							<div class="grid-cell drag-cell" v-if="draggable">
								<span
									class="drag-handle"
									v-html="utils.icon('drag', 'xs')"
									@click.stop
									@dblclick.stop="toggleGroup(row)"
								/>
							</div>

							<!-- Group Toggle/Operator -->
							<div class="grid-cell operator-cell">
								<Switch v-if="isGroupRow(row)" v-model="row.isAnd" as="template">
									<button
										class="group-switch"
										:class="{ 'is-and': row.isAnd, 'is-or': !row.isAnd }"
										@click.stop
									>
										<span class="sr-only">Toggle between AND and OR</span>
										<span class="switch-track">
											<span class="switch-thumb" />
										</span>
										<span class="switch-labels">
											<span class="label-and">{{ __("All") }}</span>
											<span class="label-or">{{ __("Any") }}</span>
										</span>
									</button>
								</Switch>

								<button
									v-if="hasChildren(row)"
									class="toggle-button"
									@click.stop="toggleGroup(row)"
									:aria-expanded="isGroupExpanded(row)"
								>
									<span aria-hidden="true">{{ isGroupExpanded(row) ? "▼" : "▶" }}</span>
								</button>
							</div>

							<!-- Group Content -->
							<div class="grid-cell summary-cell">
								<div class="group-summary">
									<span class="group-icon" v-html="utils.icon('folder', 'sm')" />
									<span class="group-label">{{ getGroupLabel(row) }}</span>
									<span class="child-count" v-if="!isGroupExpanded(row)"
										>({{ getChildCount(row) }})</span
									>
								</div>
							</div>

							<!-- Action Buttons -->
							<div class="grid-cell actions-cell">
								<div
									class="action-buttons"
									v-show="
										isRowFocused(visibleRowStart + rowIndex) ||
										hoveredRow === visibleRowStart + rowIndex
									"
								>
									<button
										class="action-button add-row"
										@click.stop="addChildRow(row)"
										aria-label="Add child row"
									>
										<span aria-hidden="true">+</span>
									</button>
									<button
										class="action-button add-group"
										@click.stop="addChildGroup(row)"
										aria-label="Add child group"
									>
										<span aria-hidden="true">⋁</span>
									</button>
									<button
										class="action-button duplicate"
										@click.stop="duplicateRow(row)"
										aria-label="Duplicate"
									>
										<span aria-hidden="true">⎘</span>
									</button>
									<button
										class="action-button delete"
										@click.stop="removeRow(row)"
										aria-label="Delete"
									>
										<span aria-hidden="true">✕</span>
									</button>
								</div>
							</div>
						</div>

						<!-- Leaf Row -->
						<div
							v-else
							class="grid-row leaf-row"
							:class="{
								'is-focused': isRowFocused(visibleRowStart + rowIndex),
								'has-parent': row[parentKeyMap.child],
								'is-dragging': draggedRow?.id === row.id,
							}"
							:style="{ paddingLeft: `${getDepth(row) * indentSize}px` }"
							role="row"
							:aria-level="getDepth(row) + 1"
							:aria-rowindex="getAriaRowIndex(rowIndex)"
							draggable="true"
							@dragstart="onDragStart($event, row)"
							@dragover.prevent="onDragOver($event, row)"
							@drop="onDrop($event, row)"
							@dragend="onDragEnd"
							@mouseenter="hoveredRow = visibleRowStart + rowIndex"
							@mouseleave="hoveredRow = null"
						>
							<div
								class="grid-cell selection-cell"
								v-if="showSelection"
								:style="{ width: getColumnWidth({ fieldname: 'selection' }) }"
							>
								<slot name="selection-cell" :row="row">
									<!-- Fallback checkbox -->
									<input
										type="checkbox"
										:checked="isRowSelected(row)"
										@change="toggleRowSelection(row)"
										@click.stop
									/>
								</slot>
							</div>

							<!-- Drag Handle -->
							<div class="grid-cell drag-cell" v-if="draggable">
								<span class="drag-handle" v-html="utils.icon('drag', 'xs')" @click.stop />
							</div>

							<!-- Empty operator cell for alignment -->
							<div class="grid-cell operator-cell"></div>

							<!-- Leaf Dynamic Fields -->
							<template v-for="(col, colIndex) in flattenedColumns" :key="col.fieldname">
								<div
									class="grid-cell"
									:style="{ width: getColumnWidth(col) }"
									v-if="!['selection', 'drag', 'operator', 'actions'].includes(col.fieldname)"
								>
									<DynamicField
										v-if="col.fieldtype"
										:df="col"
										:doc="row"
										mode="labelless"
										@field-change="onFieldChange"
									/>
									<span v-else>{{ row[col.fieldname] }}</span>
								</div>
							</template>

							<!-- Action Buttons -->
							<div class="grid-cell actions-cell">
								<div
									class="action-buttons"
									v-show="
										isRowFocused(visibleRowStart + rowIndex) ||
										hoveredRow === visibleRowStart + rowIndex
									"
								>
									<button
										class="action-button duplicate"
										@click.stop="duplicateRow(row)"
										aria-label="Duplicate"
									>
										<span aria-hidden="true">⎘</span>
									</button>
									<button
										class="action-button delete"
										@click.stop="removeRow(row)"
										aria-label="Delete"
									>
										<span aria-hidden="true">✕</span>
									</button>
								</div>
							</div>
						</div>

						<!-- Expanded Content for Leaf Rows -->
						<transition name="expand">
							<div
								v-if="!isGroupRow(row) && expandedRows.includes(row.id)"
								class="expanded-content"
								:style="{ paddingLeft: `${getDepth(row) * indentSize + 24}px` }"
							>
								<div class="condition-form">
									<GridRenderer :doc="row" :fields="rowFields" @field-change="onFieldChange" />
								</div>
							</div>
						</transition>
					</template>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick, onMounted } from "vue";
import DynamicField from "./DynamicField.vue";
import GridRenderer from "./GridRenderer.vue";
import { Switch } from "@headlessui/vue";
import draggable from "vuedraggable";
import { getServiceUIConfig, safeFrappeUtils, formatValue } from "../utils";

// ==== Props ====
const props = defineProps({
	rows: {
		type: Array,
		default: () => [],
	},
	columns: {
		type: Array,
		required: true,
	},
	groupingKeyField: {
		type: String,
		required: true,
	},
	parentKeyMap: {
		type: Object,
		default: () => ({ parent: "parent_id", child: "id" }),
	},
	showSelection: {
		type: Boolean,
		default: false,
	},
	draggable: {
		type: Boolean,
		default: true,
	},
	showItemCount: {
		type: Boolean,
		default: true,
	},
	indentSize: {
		type: Number,
		default: 20,
	},
	rowHeight: {
		type: Number,
		default: 36,
	},
	defaultGroupState: {
		type: Boolean,
		default: true,
	},
	allowCrossLevelDrag: {
		type: Boolean,
		default: true,
	},
	getGroupLabel: {
		type: Function,
		default: (row) => row.name || "Group",
	},
	getSummaryFields: {
		// Added missing prop
		type: Function,
		default: (row) => [], // Safe default
	},
	rowFields: {
		// Added missing prop
		type: Array,
		default: () => [],
	},
});

// Now we can properly initialize getSummaryFields with access to props

const effectiveRowFields = props.rowFields || [];

const emit = defineEmits([
	"update:rows",
	"row-added",
	"row-removed",
	"cell-edited",
	"group-toggle",
	"row-selected",
	"drag-drop",
	"validation-error",
]);

// ==== Refs & State ====
const gridRef = ref(null);
const gridBodyRef = ref(null);
const internalRows = ref(JSON.parse(JSON.stringify(props.rows)));
const expandedGroups = ref(new Set());
const expandedRows = ref([]);
const allGroupsExpanded = ref(props.defaultGroupState);
const visibleRowStart = ref(0);
const focusedRow = ref(null);
const hoveredRow = ref(null);
const draggedRow = ref(null);
const draggedChildren = ref([]);
const selectedRows = ref(new Set());
const colWidths = reactive({});
const utils = safeFrappeUtils();

// ==== Computed ====
const isGroupRow = (row) => !!row[props.groupingKeyField] && !!row.isGroup;

const isGroupExpanded = (groupRow) => expandedGroups.value.has(groupRow[props.parentKeyMap.child]);
const effectiveGetSummaryFields =
	props.getSummaryFields || ((row) => props.columns.filter((col) => col.showInSummary));

const flattenedRows = computed(() => {
	if (!internalRows.value || !internalRows.value.length) return [];

	const result = [];
	const queue = [
		...internalRows.value.filter(
			(row) => !row?.[props.parentKeyMap.parent] || row?.[props.parentKeyMap.parent] === "Root",
		),
	];

	while (queue.length) {
		const current = queue.shift();
		if (!current) continue;

		result.push(current);

		if (isGroupRow(current)) {
			if (isGroupExpanded(current)) {
				const children = internalRows.value
					.filter((row) => row?.[props.parentKeyMap.parent] === current?.[props.parentKeyMap.child])
					.sort((a, b) => {
						if (isGroupRow(a) && !isGroupRow(b)) return -1;
						if (!isGroupRow(a) && isGroupRow(b)) return 1;
						return 0;
					});
				queue.push(...children);
			}
		} else if (expandedRows.value.includes(current?.[props.parentKeyMap.child])) {
			// Handle expanded leaf row children if needed
		}
	}

	return result;
});

const flattenedColumns = computed(() => {
	return props.columns?.filter((col) => col) || [];
});
const totalRowCount = computed(() => flattenedRows.value.length + 1);

const visibleRowCount = computed(() => {
	if (!gridBodyRef.value) return 20;
	return Math.ceil(gridBodyRef.value.clientHeight / props.rowHeight) + 5;
});

const visibleRows = computed(() => {
	return flattenedRows.value.slice(
		visibleRowStart.value,
		visibleRowStart.value + visibleRowCount.value,
	);
});

const getDepth = (row) => {
	const parentId = row?.[props.parentKeyMap.parent];
	if (!parentId || parentId === "Root") return 0;
	const parent = internalRows.value.find((r) => r?.[props.parentKeyMap.child] === parentId);
	return parent ? getDepth(parent) + 1 : 0;
};

const getRowKey = (row) => row[props.parentKeyMap.child] || JSON.stringify(row);

const getAriaRowIndex = (visibleIndex) => visibleRowStart.value + visibleIndex + 2;

const getChildCount = (row) =>
	internalRows.value.filter((r) => r[props.parentKeyMap.parent] === row[props.parentKeyMap.child])
		.length;

const hasChildren = (row) =>
	internalRows.value.some((r) => r[props.parentKeyMap.parent] === row[props.parentKeyMap.child]);

const getColumnWidth = (col) => `${colWidths[col.fieldname] ?? col.width ?? 150}px`;

const isRowFocused = (rowIndex) => {
	return focusedRow.value === rowIndex;
};

const isRowSelected = (row) => selectedRows.value.has(row.id);

const toggleRowSelection = (row) => {
	if (selectedRows.value.has(row.id)) {
		selectedRows.value.delete(row.id);
	} else {
		selectedRows.value.add(row.id);
	}
	emit("row-selected", Array.from(selectedRows.value));
};

const toggleGroup = (row) => {
	const id = row[props.parentKeyMap.child];
	if (expandedGroups.value.has(id)) {
		expandedGroups.value.delete(id);
	} else {
		expandedGroups.value.add(id);
	}
	emit("group-toggle", { row, expanded: isGroupExpanded(row) });
};

const toggleRowExpansion = (row) => {
	if (expandedRows.value.includes(row.id)) {
		expandedRows.value = expandedRows.value.filter((id) => id !== row.id);
	} else {
		expandedRows.value.push(row.id);
	}
};

const toggleAllGroups = () => {
	allGroupsExpanded.value = !allGroupsExpanded.value;
	if (allGroupsExpanded.value) {
		internalRows.value
			.filter((row) => isGroupRow(row))
			.forEach((row) => expandedGroups.value.add(row[props.parentKeyMap.child]));
	} else {
		expandedGroups.value.clear();
	}
};

const addChildRow = (parentRow) => {
	const newRow = {
		id: generateId(),
		parent_id: parentRow.id,
		isGroup: false,
		// other default values
	};
	internalRows.value.push(newRow);
	emit("row-added", { row: newRow, parent: parentRow });
};

const addChildGroup = (parentRow) => {
	const newGroup = {
		id: generateId(),
		parent_id: parentRow.id,
		isGroup: true,
		isAnd: true,
		// other default values
	};
	internalRows.value.push(newGroup);
	expandedGroups.value.add(newGroup.id);
	emit("row-added", { row: newGroup, parent: parentRow });
};

const duplicateRow = (row) => {
	const newRow = JSON.parse(JSON.stringify(row));
	newRow.id = generateId();
	internalRows.value.push(newRow);
	emit("row-added", { row: newRow });
};

const removeRow = (row) => {
	const index = internalRows.value.findIndex((r) => r.id === row.id);
	if (index !== -1) {
		internalRows.value.splice(index, 1);
		emit("row-removed", row);
	}
};

const onFieldChange = (fieldname, value, row) => {
	row[fieldname] = value;
	emit("cell-edited", { row, fieldname, value });
};

const onDragStart = (event, row) => {
	draggedRow.value = row;
	draggedChildren.value = internalRows.value.filter(
		(r) => r[props.parentKeyMap.parent] === row[props.parentKeyMap.child],
	);
	event.dataTransfer.effectAllowed = "move";
};

const onDragOver = (event, targetRow) => {
	event.preventDefault();
	// Visual feedback can be added here
};

const onDrop = (event, targetRow) => {
	event.preventDefault();
	if (!draggedRow.value) return;

	if (props.allowCrossLevelDrag || getDepth(targetRow) === getDepth(draggedRow.value)) {
		draggedRow.value[props.parentKeyMap.parent] = targetRow[props.parentKeyMap.child];
		emit("drag-drop", { draggedRow: draggedRow.value, targetRow });
	}

	draggedRow.value = null;
	draggedChildren.value = [];
};

const onDragEnd = () => {
	draggedRow.value = null;
	draggedChildren.value = [];
};

const handleScroll = (event) => {
	if (!gridBodyRef.value) return;
	const scrollTop = gridBodyRef.value.scrollTop;
	visibleRowStart.value = Math.floor(scrollTop / props.rowHeight);
};

const generateId = () => {
	return Math.random().toString(36).substring(2, 15);
};

// ==== Lifecycle ====

// Define initColWidths function
const initColWidths = () => {
	if (!props.columns || !props.columns.length) return;

	props.columns.forEach((col) => {
		if (!col) return;

		if (!colWidths[col.fieldname]) {
			colWidths[col.fieldname] = col.width ?? 150;
		}

		if (col.group && col.columns && col.columns.length) {
			col.columns.forEach((subCol) => {
				if (!subCol) return;
				if (!colWidths[subCol.fieldname]) {
					colWidths[subCol.fieldname] = subCol.width ?? 150;
				}
			});
		}
	});
};

onMounted(() => {
	initColWidths(); // Call the function
	if (props.defaultGroupState) {
		internalRows.value
			.filter((row) => isGroupRow(row))
			.forEach((row) => expandedGroups.value.add(row[props.parentKeyMap.child]));
	}
});

watch(
	() => props.columns,
	() => {
		initColWidths(); // Call the function when columns change
	},
	{ deep: true },
);

watch(
	() => props.rows,
	(val) => {
		internalRows.value = JSON.parse(JSON.stringify(val));
	},
	{ deep: true },
);
</script>

<style scoped>
/* Base Variables */
:root {
	--row-height: 36px;
	--icon-size: 14px;
	--border-radius: 4px;
	--transition-speed: 0.15s;
	--color-primary: #3b82f6;
	--color-danger: #ef4444;
	--color-success: #10b981;
	--color-warning: #f59e0b;
	--color-text: #334155;
	--color-text-light: #64748b;
	--color-bg-hover: #f8fafc;
	--color-border: #e2e8f0;
	--color-bg-active: #f1f5f9;
	--focus-ring: 0 0 0 2px #bfdbfe;
}

.nested-grid-container {
	display: flex;
	flex-direction: column;
	height: 100%;
	overflow: hidden;
}

.nested-editable-grid {
	display: flex;
	flex-direction: column;
	border: 1px solid var(--color-border);
	border-radius: var(--border-radius);
	overflow: hidden;
	flex-grow: 1;
	background: white;
}

/* Header Styles */
.grid-header {
	display: flex;
	background: #f5f5f5;
	border-bottom: 1px solid var(--color-border);
}

.grid-header-cell {
	position: relative;
	padding: 8px;
	border-right: 1px solid var(--color-border);
	font-weight: 600;
	font-size: 0.8125rem;
	color: var(--color-text);
}

.header-content {
	display: flex;
	align-items: center;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.resize-handle {
	position: absolute;
	top: 0;
	right: 0;
	width: 5px;
	height: 100%;
	cursor: col-resize;
	background: transparent;
}

.resize-handle:hover {
	background: var(--color-primary);
	opacity: 0.3;
}

/* Body Styles */
.grid-body {
	overflow-y: auto;
	position: relative;
	flex-grow: 1;
}

.grid-body-content {
	position: absolute;
	width: 100%;
}

/* Row Styles */
.grid-row {
	display: flex;
	align-items: center;
	height: var(--row-height);
	border-bottom: 1px solid var(--color-border);
	background: white;
	transition: all var(--transition-speed) ease;
	cursor: pointer;
	font-size: 0.8125rem;
}

.grid-row:hover {
	background-color: var(--color-bg-hover);
}

.grid-row.is-focused {
	border-color: var(--color-primary);
	box-shadow: var(--focus-ring);
}

.grid-row.is-dragging {
	opacity: 0.5;
	background-color: #ebf8ff;
	border-color: #bee3f8;
}

/* Group Row Specific */
.group-row {
	background: #f9f9f9;
	font-weight: 600;
}

.group-row.expanded {
	background: #f0f7ff;
}

/* Cell Styles */
.grid-cell {
	padding: 0 8px;
	border-right: 1px solid var(--color-border);
	height: 100%;
	display: flex;
	align-items: center;
	overflow: hidden;
}

.selection-cell {
	justify-content: center;
	flex: 0 0 24px;
}

.drag-cell {
	justify-content: center;
	flex: 0 0 24px;
}

.operator-cell {
	justify-content: flex-start;
	flex: 0 0 60px;
}

.summary-cell {
	flex: 1 1 auto;
	overflow: visible;
}

.actions-cell {
	justify-content: flex-end;
	flex: 0 0 auto;
}

/* Drag Handle */
.drag-handle {
	opacity: 0.3;
	cursor: grab;
	transition: all var(--transition-speed) ease;
	padding: 4px;
	font-size: var(--icon-size);
	color: var(--color-text-light);
}

.grid-row:hover .drag-handle,
.grid-row.is-focused .drag-handle {
	opacity: 0.8;
	color: var(--color-text);
}

/* Toggle Button */
.toggle-button {
	width: 30px;
	height: 20px;
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 3px;
	background: none;
	border: none;
	color: var(--color-text-light);
	cursor: pointer;
	transition: all var(--transition-speed) ease;
	font-size: var(--icon-size);
}

.toggle-button:hover {
	color: var(--color-primary);
	background-color: var(--color-bg-active);
}

/* Group Summary */
.group-summary,
.leaf-summary {
	display: flex;
	align-items: center;
	gap: 6px;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.group-icon,
.leaf-icon {
	font-size: var(--icon-size);
	flex-shrink: 0;
}

.group-icon {
	color: var(--color-warning);
}

.leaf-icon {
	color: var(--color-primary);
}

.child-count {
	color: var(--color-text-light);
	font-size: 0.75em;
}

.summary-fields {
	display: flex;
	flex-wrap: nowrap;
	gap: 8px;
	align-items: center;
	overflow: visible;
}

/* Action Buttons */
.action-buttons {
	display: flex;
	gap: 4px;
	padding: 2px;
}

.action-button {
	width: 24px;
	height: 24px;
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 4px;
	border: 1px solid transparent;
	background: none;
	cursor: pointer;
	transition: all var(--transition-speed) ease;
	font-size: var(--icon-size);
	color: var(--color-text-light);
}

.action-button:hover {
	background-color: var(--color-bg-active);
	border-color: var(--color-border);
	color: var(--color-text);
}

.action-button.add-row {
	color: var(--color-success);
}
.action-button.add-row:hover {
	background-color: rgba(16, 185, 129, 0.1);
}

.action-button.add-group {
	color: var(--color-warning);
}
.action-button.add-group:hover {
	background-color: rgba(245, 158, 11, 0.1);
}

.action-button.duplicate {
	color: var(--color-primary);
}
.action-button.duplicate:hover {
	background-color: rgba(59, 130, 246, 0.1);
}

.action-button.delete {
	color: var(--color-danger);
}
.action-button.delete:hover {
	background-color: rgba(239, 68, 68, 0.1);
}

/* Group Switch Toggle */
.group-switch {
	--switch-width: 60px;
	--switch-height: 24px;
	--thumb-size: 18px;
	--thumb-offset: 2px;

	position: relative;
	width: var(--switch-width);
	height: var(--switch-height);
	display: inline-block;
	border: none;
	background: transparent;
	padding: 0;
	cursor: pointer;
}

.switch-track {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	border-radius: 12px;
	background-color: var(--color-bg-active);
	border: 1px solid var(--color-border);
	transition: all var(--transition-speed) ease;
}

.switch-thumb {
	position: absolute;
	top: var(--thumb-offset);
	left: var(--thumb-offset);
	width: var(--thumb-size);
	height: var(--thumb-size);
	border-radius: 50%;
	background-color: white;
	box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
	transition: transform var(--transition-speed) ease;
	z-index: 2;
}

.switch-labels {
	position: relative;
	display: flex;
	height: 100%;
	z-index: 1;
}

.label-and,
.label-or {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 0.6875rem;
	font-weight: 600;
	text-transform: uppercase;
	color: var(--color-text-light);
	transition: color var(--transition-speed) ease;
}

/* AND State */
.is-and .switch-track {
	background-color: rgba(16, 185, 129, 0.1);
	border-color: rgba(16, 185, 129, 0.3);
}

.is-and .switch-thumb {
	transform: translateX(calc(var(--switch-width) - var(--thumb-size) - (var(--thumb-offset) * 2)));
	background-color: var(--color-success);
}

.is-and .label-and {
	color: var(--color-success);
	font-weight: 700;
}

/* OR State */
.is-or .switch-track {
	background-color: rgba(245, 158, 11, 0.1);
	border-color: rgba(245, 158, 11, 0.3);
}

.is-or .switch-thumb {
	transform: translateX(var(--thumb-offset));
	background-color: var(--color-warning);
}

.is-or .label-or {
	color: var(--color-warning);
	font-weight: 700;
}

.group-switch:focus-visible {
	outline: 2px solid var(--color-primary);
	outline-offset: 2px;
	border-radius: 14px;
}

/* Expanded Content */
.expand-enter-active,
.expand-leave-active {
	transition: all var(--transition-speed) ease;
	overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
	opacity: 0;
	transform: translateY(-5px);
	max-height: 0;
}

.expanded-content {
	border-left: 1px dashed var(--color-border);
	margin-left: 3px;
}

.condition-form {
	padding: 8px;
	margin-top: 0px;
	border: 1px solid var(--color-border);
	border-radius: var(--border-radius);
	background: var(--color-bg-hover);
}

/* Checkbox */
input[type="checkbox"] {
	width: 14px;
	height: 14px;
	cursor: pointer;
	accent-color: var(--color-primary);
}

/* Accessibility */
.sr-only {
	position: absolute;
	width: 1px;
	height: 1px;
	padding: 0;
	margin: -1px;
	overflow: hidden;
	clip: rect(0, 0, 0, 0);
	white-space: nowrap;
	border-width: 0;
}

/* Focus States */
.action-button:focus-visible,
.toggle-button:focus-visible,
.drag-handle:focus-visible,
.group-switch:focus-visible {
	outline: 2px solid var(--color-primary);
	outline-offset: 1px;
}

/* Scrollbar styling */
.grid-body::-webkit-scrollbar {
	height: 8px;
	width: 8px;
}

.grid-body::-webkit-scrollbar-track {
	background: #f1f1f1;
}

.grid-body::-webkit-scrollbar-thumb {
	background: #c1c1c1;
	border-radius: 4px;
}

.grid-body::-webkit-scrollbar-thumb:hover {
	background: #a8a8a8;
}

/* Ensure dropdowns and other popups aren't clipped */
.grid-row,
.grid-cell,
.summary-fields,
.expanded-content {
	overflow: visible !important;
	contain: none !important;
}
</style>
