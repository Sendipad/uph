<template>
	<div
		class="editable-grid"
		tabindex="0"
		@keydown="onKeydown"
		@paste="handlePaste"
		ref="gridRef"
		role="grid"
		:aria-rowcount="rows.length + 1 + (newRowMode === 'form' && isAddingRow ? 1 : 0)"
		:aria-colcount="flattenedColumns.length"
	>
		<div aria-live="polite" aria-atomic="true" class="sr-only">
			{{ a11yAnnouncement }}
		</div>
		<div class="grid-header" role="row" aria-rowindex="1">
			<template v-for="(col, index) in flattenedColumns" :key="col.fieldname || col.label">
				<div
					v-if="col.group"
					class="group-header"
					:style="{ width: getGroupWidth(col) + 'px' }"
					role="columnheader"
					:aria-colspan="col.columns.length"
				>
					{{ col.label }}
				</div>
				<draggable
					v-else
					v-model="columns"
					item-key="fieldname"
					tag="div"
					class="grid-header-cell"
					:style="{ width: colWidths[col.fieldname] + 'px' }"
					:data-index="getOriginalColumnIndex(col.fieldname)"
					role="columnheader"
					:aria-colindex="index + 1"
					@mousedown.stop
				>
					<template #item="{ element: col }">
						<div class="header-content" @click="focusColumn(getOriginalColumnIndex(col.fieldname))">
							<span class="col-drag-handle" title="Drag to reorder column">⇅</span>
							{{ col.label }}
							<span v-if="col.mandatory" class="mandatory-star" title="Mandatory">*</span>
						</div>
						<div
							class="resize-handle"
							@mousedown.prevent="initResize($event, col.fieldname)"
							title="Resize column"
						/>
					</template>
				</draggable>
			</template>
		</div>
		<div v-if="rows.length === 0" class="empty-state-container">
			<slot name="empty-state">
				<div class="default-empty-state">
					<svg class="empty-icon" viewBox="0 0 24 24">
						<path
							fill="currentColor"
							d="M19,3H5C3.89,3 3,3.89 3,5V19C3,20.1 3.9,21 5,21H19C20.1,21 21,20.1 21,19V5C21,3.89 20.1,3 19,3M19,5V19H5V5H19M7,7H17V9H7V7M7,11H17V13H7V11M7,15H14V17H7V15Z"
						/>
					</svg>
					<h3>No Data Available</h3>
					<button @click="addRowManually">Add First Row</button>
				</div>
			</slot>
		</div>
		<div
			class="grid-body"
			@scroll="handleScroll"
			ref="gridBodyRef"
			:style="{ height: `${rows.length * rowHeight}px` }"
			role="rowgroup"
		>
			<div
				class="grid-body-content"
				:style="{ transform: `translateY(${visibleRowStart * rowHeight}px)` }"
			>
				<draggable
					v-model="visibleRows"
					item-key="rowId"
					tag="div"
					handle=".row-drag-handle"
					:animation="150"
					@end="onRowsReordered"
					role="row"
				>
					<template #item="{ element: row, index: visibleIndex }">
						<div
							class="grid-row"
							:class="{
								focused: isRowFocused(visibleRowStart + visibleIndex),
								'row-error': showValidation && hasRowErrors(visibleRowStart + visibleIndex),
							}"
							@click="focusRow(visibleRowStart + visibleIndex)"
							role="row"
							:aria-rowindex="visibleRowStart + visibleIndex + 2"
						>
							<div
								class="row-drag-handle"
								title="Drag to reorder row"
								aria-label="Drag handle"
								tabindex="-1"
							>
								☰
							</div>
							<template v-for="(col, cIndex) in columns" :key="col.fieldname">
								<div
									class="grid-cell"
									:style="{ width: colWidths[col.fieldname] + 'px' }"
									:class="{
										focused: isCellFocused(visibleRowStart + visibleIndex, cIndex),
										invalid:
											showValidation && isInvalidCell(visibleRowStart + visibleIndex, cIndex),
									}"
									@click.stop="focusCell(visibleRowStart + visibleIndex, cIndex)"
									@mouseenter="
										showTooltip($event, getTooltipContent(visibleRowStart + visibleIndex, cIndex))
									"
									@mouseleave="hideTooltip"
									role="gridcell"
									:aria-colindex="cIndex + 1"
									:aria-readonly="
										(
											overridesCache.get(`${visibleRowStart + visibleIndex}-${col.fieldname}`)
												?.read_only ?? col.read_only
										).toString()
									"
									:aria-required="
										(
											overridesCache.get(`${visibleRowStart + visibleIndex}-${col.fieldname}`)
												?.mandatory ?? col.mandatory
										).toString()
									"
									:aria-invalid="isInvalidCell(visibleRowStart + visibleIndex, cIndex)"
								>
									<template v-if="isCellFocused(visibleRowStart + visibleIndex, cIndex)">
										<component
											:is="getInputComponent(col.fieldtype)"
											v-model="rows[visibleRowStart + visibleIndex][col.fieldname]"
											:options="
												overridesCache.get(`${visibleRowStart + visibleIndex}-${col.fieldname}`)
													?.options ?? parseOptions(col.options)
											"
											:readonly="
												overridesCache.get(`${visibleRowStart + visibleIndex}-${col.fieldname}`)
													?.read_only ?? col.read_only
											"
											:aria-label="`Edit ${col.label} row ${visibleRowStart + visibleIndex + 1}`"
											@blur="onCellBlur"
											@keydown.stop.prevent="
												onInputKeydown($event, visibleRowStart + visibleIndex, cIndex)
											"
											ref="el => setInputRef(visibleRowStart + visibleIndex, cIndex, el)"
											class="cell-input"
										/>
									</template>
									<template v-else>
										<template v-if="cellRenderer">
											<component
												:is="
													cellRenderer({
														row,
														column: col,
														value: row[col.fieldname],
														rowIndex: visibleRowStart + visibleIndex,
														colIndex: cIndex,
													})
												"
											/>
										</template>
										<template v-else>
											{{ formatValue(row[col.fieldname], col.fieldtype) }}
										</template>
									</template>
								</div>
							</template>
							<button
								type="button"
								class="remove-row-btn"
								aria-label="Remove row"
								@click.stop="removeRow(visibleRowStart + visibleIndex)"
							>
								✕
							</button>
						</div>
					</template>
				</draggable>
			</div>
		</div>
		<div v-if="isTooltipOpen" class="grid-tooltip" tooltipStyles ref="tooltipRef">
			{{ tooltipContent }}
		</div>
		<div
			v-if="isAddingRow && newRowMode === 'form'"
			class="new-row-form"
			role="form"
			aria-label="New Row Form"
		>
			<h3>New Row</h3>
			<div v-for="(col, cIndex) in columns" :key="col.fieldname" class="form-field">
				<label :for="`new-row-${col.fieldname}`">{{ col.label }}</label>
				<component
					:is="getInputComponent(col.fieldtype)"
					v-model="newRow[col.fieldname]"
					:options="parseOptions(col.options)"
					:readonly="col.read_only"
					:id="`new-row-${col.fieldname}`"
					class="form-input"
					@keydown.enter.prevent="saveNewRow"
					:aria-invalid="isInvalidNewRowField(col.fieldname)"
				/>
				<span v-if="showValidation && isInvalidNewRowField(col.fieldname)" class="error-message">
					Invalid value
				</span>
			</div>
			<div class="form-actions">
				<button @click="saveNewRow" class="primary">Save</button>
				<button @click="cancelNewRow" class="secondary">Cancel</button>
			</div>
		</div>
		<div class="grid-controls" v-if="!isAddingRow || newRowMode === 'grid'">
			<button type="button" @click="addRowManually" class="primary">Add Row</button>
			<button type="button" @click="addColumn" class="secondary">Add Column</button>
		</div>
	</div>
</template>

<script setup>
import { ref, reactive, watch, nextTick, computed, onMounted } from "vue";
import draggable from "vuedraggable";
import { debounce } from "lodash-es";

const props = defineProps({
	modelValue: {
		type: Array,
		default: () => [],
	},
	columns: {
		type: Array,
		required: true,
	},
	getDynamicFieldOverrides: {
		type: Function,
		default: () => () => ({}),
	},
	newRowMode: {
		type: String,
		default: "grid",
		validator: (v) => ["grid", "form"].includes(v),
	},
	cellRenderer: {
		type: Function,
		default: null,
	},
});

const emit = defineEmits([
	"update:modelValue",
	"row-added",
	"column-added",
	"cell-edited",
	"row-removed",
	"columns-reordered",
	"rows-reordered",
	"validation-error",
]);

const rows = ref(JSON.parse(JSON.stringify(props.modelValue || [])));
const columns = ref(JSON.parse(JSON.stringify(props.columns || [])));
const defaultColWidth = 150;
const colWidths = reactive({});
const gridRef = ref(null);
const gridBodyRef = ref(null);

const rowHeight = 40;
const visibleRowStart = ref(0);
const scrollTop = ref(0);

const focusedCell = reactive({ row: null, col: null });
const focusedRow = ref(null);
const inputRefs = new Map();

const showValidation = ref(false);
const tooltipRef = ref(null);
const tooltipTarget = ref(null); // the element tooltip relates to

const tooltip = ref(null);
const isTooltipOpen = ref(false);
const tooltipContent = ref("");
const { floatingStyles, update } = useFloating(tooltip, {
	whileElementsMounted: autoUpdate,
	placement: "top",
	middleware: [offset(5), flip(), shift()],
});

const a11yAnnouncement = ref("");

const isAddingRow = ref(false);
const newRow = reactive({});

const visibleRowCount = computed(() => {
	if (!gridBodyRef.value) return 20;
	return Math.ceil(gridBodyRef.value.clientHeight / rowHeight) + 5;
});

const visibleRows = computed(() => {
	return rows.value.slice(visibleRowStart.value, visibleRowStart.value + visibleRowCount.value);
});
const tooltipStyles = reactive({
	top: "0px",
	left: "0px",
	position: "absolute",
	zIndex: 1000,
});

function showTooltip(event, content) {
	tooltipTarget.value = event.currentTarget;
	tooltipContent.value = content;
	isTooltipOpen.value = true;

	nextTick(() => {
		if (!tooltipRef.value || !tooltipTarget.value) return;

		const targetRect = tooltipTarget.value.getBoundingClientRect();
		const tooltipRect = tooltipRef.value.getBoundingClientRect();

		// Simple positioning above the target, centered horizontally
		tooltipStyles.top = `${targetRect.top - tooltipRect.height - 8 + window.scrollY}px`;
		tooltipStyles.left = `${targetRect.left + (targetRect.width - tooltipRect.width) / 2 + window.scrollX}px`;
	});
}

const flattenedColumns = computed(() => {
	const flat = [];
	columns.value.forEach((col) => {
		if (col.group) {
			flat.push(col);
			flat.push(...col.columns);
		} else {
			flat.push(col);
		}
	});
	return flat;
});

const overridesCache = computed(() => {
	const cache = new Map();
	rows.value.forEach((row, rowIndex) => {
		columns.value.forEach((col) => {
			const key = `${rowIndex}-${col.fieldname}`;
			const overrides = props.getDynamicFieldOverrides(row, col.fieldname) || {};
			cache.set(key, overrides);
		});
	});
	return cache;
});

function initColWidths() {
	columns.value.forEach((col) => {
		if (!colWidths[col.fieldname]) colWidths[col.fieldname] = col.width || defaultColWidth;
	});
}

onMounted(() => {
	initColWidths();
	const savedColumns = localStorage.getItem("gridColumns");
	if (savedColumns) columns.value = JSON.parse(savedColumns);
});

watch(
	() => props.modelValue,
	(newVal) => {
		rows.value = JSON.parse(JSON.stringify(newVal || []));
	},
);

watch(
	() => props.columns,
	(newCols) => {
		columns.value = JSON.parse(JSON.stringify(newCols || []));
		initColWidths();
	},
);

watch(
	rows,
	debounce((newVal) => {
		emit("update:modelValue", newVal);
	}, 300),
	{ deep: true },
);

let resizingCol = null;
let startX = 0;
let startWidth = 0;

function initResize(event, fieldname) {
	resizingCol = fieldname;
	startX = event.clientX;
	startWidth = colWidths[fieldname];
	window.addEventListener("mousemove", resizeCol);
	window.addEventListener("mouseup", stopResize);
}

function resizeCol(event) {
	if (!resizingCol) return;
	const delta = event.clientX - startX;
	const newWidth = Math.max(40, startWidth + delta);
	colWidths[resizingCol] = newWidth;
}

function stopResize() {
	resizingCol = null;
	window.removeEventListener("mousemove", resizeCol);
	window.removeEventListener("mouseup", stopResize);
}

function focusCell(row, col) {
	focusedCell.row = row;
	focusedCell.col = col;
	focusedRow.value = row;
	nextTick(() => {
		const inputEl = getInputRef(row, col);
		if (inputEl) inputEl.focus();
	});
}

function isCellFocused(row, col) {
	return focusedCell.row === row && focusedCell.col === col;
}

function focusRow(row) {
	focusedRow.value = row;
}

function isRowFocused(row) {
	return focusedRow.value === row;
}

function blurCell() {
	focusedCell.row = null;
	focusedCell.col = null;
}

function onCellBlur() {
	blurCell();
}

function setInputRef(row, col, el) {
	if (el) inputRefs.set(`${row}-${col}`, el);
	else inputRefs.delete(`${row}-${col}`);
}

function getInputRef(row, col) {
	return inputRefs.get(`${row}-${col}`);
}

function onKeydown(e) {
	if (focusedCell.row === null || focusedCell.col === null) return;

	const row = focusedCell.row;
	const col = focusedCell.col;

	if (e.key === "ArrowRight") {
		if (col + 1 < columns.value.length) focusCell(row, col + 1);
	} else if (e.key === "ArrowLeft") {
		if (col - 1 >= 0) focusCell(row, col - 1);
	} else if (e.key === "ArrowDown") {
		if (row + 1 < rows.value.length) focusCell(row + 1, col);
	} else if (e.key === "ArrowUp") {
		if (row - 1 >= 0) focusCell(row - 1, col);
	} else if (e.key === "Enter") {
	} else if (e.key === "Escape") {
		blurCell();
	} else if (e.key === "Tab") {
		trapFocus(e);
	}
}

function onInputKeydown(e, row, col) {
	if (e.key === "Enter") {
		blurCell();
		if (row + 1 < rows.value.length) focusCell(row + 1, col);
	} else if (e.key === "Tab") {
		e.preventDefault();
		const isLastRow = row === rows.value.length - 1;
		const isLastCol = col === columns.value.length - 1;
		if (isLastRow && isLastCol) {
			if (props.newRowMode === "grid") {
				addRow();
				nextTick(() => {
					focusCell(rows.value.length - 1, 0);
				});
			} else if (props.newRowMode === "form") {
				startAddingRowForm();
			}
		} else {
			if (col + 1 < columns.value.length) {
				focusCell(row, col + 1);
			} else if (row + 1 < rows.value.length) {
				focusCell(row + 1, 0);
			}
		}
	}
}

function onRowsReordered(evt) {
	emit("rows-reordered", rows.value);
	emit("update:modelValue", rows.value);
}

function onColumnsReordered(evt) {
	initColWidths();
	localStorage.setItem("gridColumns", JSON.stringify(columns.value));
	emit("columns-reordered", columns.value);
}

function addRow() {
	const newRow = {};
	columns.value.forEach((col) => {
		newRow[col.fieldname] =
			col.default !== undefined ? col.default : getDefaultValue(col.fieldtype);
	});
	newRow.rowId = rows.value.length ? Math.max(...rows.value.map((r) => r.rowId || 0)) + 1 : 1;
	rows.value.push(newRow);
	announce(`Added new row at position ${rows.value.length}`);
	emit("row-added", newRow);
}

function addRowManually() {
	if (props.newRowMode === "form") {
		startAddingRowForm();
	} else {
		addRow();
	}
}

function removeRow(index) {
	const removed = rows.value.splice(index, 1)[0];
	announce(`Removed row at position ${index + 1}`);
	emit("row-removed", removed);
	emit("update:modelValue", rows.value);
}

function addColumn() {
	const newFieldIndex = columns.value.length + 1;
	const newField = {
		fieldname: `field_${newFieldIndex}`,
		label: `Field ${newFieldIndex}`,
		fieldtype: "Data",
	};
	columns.value.push(newField);
	colWidths[newField.fieldname] = defaultColWidth;
	rows.value.forEach((row) => {
		row[newField.fieldname] = "";
	});
	announce(`Added new column ${newField.label}`);
	emit("column-added", newField);
}

function startAddingRowForm() {
	isAddingRow.value = true;
	columns.value.forEach((col) => {
		newRow[col.fieldname] =
			col.default !== undefined ? col.default : getDefaultValue(col.fieldtype);
	});
}

function saveNewRow() {
	if (!validateBeforeSave()) {
		emit("validation-error", getValidationErrors());
		announce("Validation errors - please fix before saving");
		return;
	}

	const newRowCopy = {};
	columns.value.forEach((col) => {
		newRowCopy[col.fieldname] = newRow[col.fieldname];
	});
	newRowCopy.rowId = rows.value.length ? Math.max(...rows.value.map((r) => r.rowId || 0)) + 1 : 1;
	rows.value.push(newRowCopy);
	announce(`Added new row at position ${rows.value.length}`);
	emit("row-added", newRowCopy);
	isAddingRow.value = false;

	if (props.newRowMode === "grid") {
		nextTick(() => {
			focusCell(rows.value.length - 1, 0);
		});
	}
}

function cancelNewRow() {
	isAddingRow.value = false;
	announce("Cancelled adding new row");
}

function validateBeforeSave() {
	showValidation.value = true;
	const isValid =
		rows.value.every((row, rowIndex) =>
			columns.value.every((col, colIndex) => !isInvalidCell(rowIndex, colIndex)),
		) &&
		(!isAddingRow.value || validateNewRowForm());

	if (!isValid) {
		emit("validation-error", getValidationErrors());
	}

	return isValid;
}

function validateNewRowForm() {
	return columns.value.every((col) => !isInvalidNewRowField(col.fieldname));
}

function isInvalidNewRowField(fieldname) {
	const col = columns.value.find((c) => c.fieldname === fieldname);
	if (!col) return false;

	const value = newRow[fieldname];

	if (col.mandatory && (value === null || value === undefined || value === "")) return true;

	if (col.fieldtype === "Int" && isNaN(parseInt(value))) return true;

	if (col.fieldtype === "Float" && isNaN(parseFloat(value))) return true;

	return false;
}

function isInvalidCell(rowIndex, colIndex) {
	const col = columns.value[colIndex];
	const value = rows.value[rowIndex]?.[col.fieldname];

	if (col.mandatory && (value === null || value === undefined || value === "")) return true;

	if (col.fieldtype === "Int" && isNaN(parseInt(value))) return true;

	if (col.fieldtype === "Float" && isNaN(parseFloat(value))) return true;

	return false;
}

function hasRowErrors(rowIndex) {
	return columns.value.some((col, colIndex) => isInvalidCell(rowIndex, colIndex));
}

function getValidationErrors() {
	const errors = [];

	rows.value.forEach((row, rowIndex) => {
		columns.value.forEach((col, colIndex) => {
			if (isInvalidCell(rowIndex, colIndex)) {
				errors.push({
					rowIndex,
					colIndex,
					fieldname: col.fieldname,
					message: `Invalid value in row ${rowIndex + 1}, column ${col.label}`,
				});
			}
		});
	});

	if (isAddingRow.value) {
		columns.value.forEach((col) => {
			if (isInvalidNewRowField(col.fieldname)) {
				errors.push({
					rowIndex: "new",
					fieldname: col.fieldname,
					message: `Invalid value in new row, column ${col.label}`,
				});
			}
		});
	}

	return errors;
}

function handleScroll(e) {
	scrollTop.value = e.target.scrollTop;
	visibleRowStart.value = Math.floor(scrollTop.value / rowHeight);
}

function handlePaste(e) {
	if (focusedCell.row === null || focusedCell.col === null) return;

	const pasteData = e.clipboardData.getData("text");
	const rowsData = pasteData.split("\n").map((row) => row.split("\t"));

	let currentRow = focusedCell.row;
	let currentCol = focusedCell.col;

	rowsData.forEach((row, rowOffset) => {
		row.forEach((cell, colOffset) => {
			const targetRow = currentRow + rowOffset;
			const targetCol = currentCol + colOffset;

			if (targetRow < rows.value.length && targetCol < columns.value.length) {
				const col = columns.value[targetCol];
				rows.value[targetRow][col.fieldname] = convertPastedValue(cell, col.fieldtype);
			}
		});
	});

	e.preventDefault();
}

function convertPastedValue(value, fieldtype) {
	switch (fieldtype) {
		case "Int":
			return parseInt(value) || 0;
		case "Float":
			return parseFloat(value) || 0;
		case "Check":
			return value.toLowerCase() === "true";
		default:
			return value;
	}
}

function hideTooltip() {
	isTooltipOpen.value = false;
}

function getTooltipContent(rowIndex, colIndex) {
	if (isInvalidCell(rowIndex, colIndex)) {
		return "Invalid value - please correct";
	}
	const col = columns.value[colIndex];
	return String(rows.value[rowIndex]?.[col.fieldname] || "Empty");
}

function announce(message) {
	a11yAnnouncement.value = message;
	setTimeout(() => (a11yAnnouncement.value = ""), 100);
}

function trapFocus(e) {
	if (!gridRef.value) return;

	const focusable = [
		...gridRef.value.querySelectorAll(
			'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
		),
	].filter((el) => !el.disabled && el.offsetParent !== null);

	if (focusable.length === 0) return;

	const first = focusable[0];
	const last = focusable[focusable.length - 1];

	if (e.key === "Tab") {
		if (e.shiftKey && document.activeElement === first) {
			last.focus();
			e.preventDefault();
		} else if (!e.shiftKey && document.activeElement === last) {
			first.focus();
			e.preventDefault();
		}
	}
}

function getDefaultValue(fieldtype) {
	switch (fieldtype) {
		case "Int":
		case "Float":
		case "Currency":
			return 0;
		case "Check":
			return false;
		case "Date":
			return null;
		default:
			return "";
	}
}

function formatValue(value, fieldtype) {
	if (value == null) return "";
	switch (fieldtype) {
		case "Date":
			return new Date(value).toLocaleDateString();
		case "Float":
		case "Currency":
			return parseFloat(value).toFixed(2);
		case "Int":
			return parseInt(value);
		case "Check":
			return value ? "✔" : "";
		default:
			return String(value);
	}
}

function parseOptions(options) {
	if (!options) return [];
	if (Array.isArray(options)) return options;
	if (typeof options === "string") {
		return options.includes("\n") ? options.split("\n") : options.split(",");
	}
	return [];
}

function getInputComponent(fieldtype) {
	switch (fieldtype) {
		case "Int":
		case "Float":
		case "Currency":
			return "input-number";
		case "Date":
			return "input-date";
		case "Select":
			return "select-input";
		case "Check":
			return "input-checkbox";
		case "Link":
			return "input-link";
		default:
			return "input-text";
	}
}

function getGroupWidth(group) {
	return group.columns.reduce((sum, col) => sum + colWidths[col.fieldname], 0);
}

function getOriginalColumnIndex(fieldname) {
	return columns.value.findIndex((col) => col.fieldname === fieldname);
}
</script>

<style scoped>
.editable-grid {
	--grid-border-color: #ddd;
	--grid-header-bg: #f5f5f5;
	--grid-row-even: #fff;
	--grid-row-odd: #f9f9f9;
	--grid-focus-border: 2px solid #4285f4;
	--grid-invalid-border: 1px solid #ff4444;
	--grid-error-bg: #fff0f0;
	--grid-group-header-bg: #e0e0e0;
	--primary-color: #4285f4;
	--primary-hover: #3367d6;
	--danger-color: #ff4444;
	--text-color: #333;
	--border-radius: 4px;

	border: 1px solid var(--grid-border-color);
	outline: none;
	user-select: none;
	font-family: Arial, sans-serif;
	color: var(--text-color);
	position: relative;
}

.grid-header {
	display: flex;
	background: var(--grid-header-bg);
	position: sticky;
	top: 0;
	z-index: 10;
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.group-header {
	padding: 8px;
	font-weight: bold;
	text-align: center;
	background: var(--grid-group-header-bg);
	border-right: 1px solid var(--grid-border-color);
	border-bottom: 1px solid var(--grid-border-color);
}

.grid-header-cell {
	position: relative;
	border-right: 1px solid var(--grid-border-color);
	border-bottom: 1px solid var(--grid-border-color);
}

.header-content {
	padding: 8px;
	display: flex;
	align-items: center;
	cursor: pointer;
}

.col-drag-handle {
	margin-right: 6px;
	cursor: move;
	opacity: 0.5;
	font-size: 0.9em;
}

.col-drag-handle:hover {
	opacity: 1;
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
	background: var(--primary-color);
	opacity: 0.3;
}

.mandatory-star {
	color: var(--danger-color);
	margin-left: 4px;
}

.grid-body {
	overflow-y: auto;
	position: relative;
}

.grid-body-content {
	position: absolute;
	width: 100%;
}

.grid-row {
	display: flex;
	height: var(--row-height, 40px);
	border-bottom: 1px solid var(--grid-border-color);
}

.grid-row:nth-child(even) {
	background: var(--grid-row-even);
}

.grid-row:nth-child(odd) {
	background: var(--grid-row-odd);
}

.grid-row.focused {
	background-color: #f0f7ff;
}

.grid-row.row-error {
	background-color: var(--grid-error-bg);
}

.row-drag-handle {
	width: 40px;
	display: flex;
	align-items: center;
	justify-content: center;
	cursor: move;
	position: sticky;
	left: 0;
	z-index: 1;
	background: inherit;
	border-right: 1px solid var(--grid-border-color);
}

.grid-cell {
	padding: 8px;
	border-right: 1px solid var(--grid-border-color);
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
	display: flex;
	align-items: center;
	position: relative;
}

.grid-cell.focused {
	outline: var(--grid-focus-border);
	z-index: 2;
}

.grid-cell.invalid {
	border: var(--grid-invalid-border);
}

.cell-input {
	width: 100%;
	border: none;
	background: transparent;
	outline: none;
}

.remove-row-btn {
	background: none;
	border: none;
	cursor: pointer;
	color: var(--danger-color);
	padding: 0 12px;
	opacity: 0.5;
}

.remove-row-btn:hover {
	opacity: 1;
}

.empty-state-container {
	display: flex;
	justify-content: center;
	padding: 40px;
	text-align: center;
}

.default-empty-state {
	max-width: 300px;
}

.empty-icon {
	width: 64px;
	height: 64px;
	margin-bottom: 16px;
	opacity: 0.5;
	color: var(--text-color);
}

.grid-controls {
	padding: 12px;
	display: flex;
	gap: 8px;
	border-top: 1px solid var(--grid-border-color);
}

button {
	padding: 6px 12px;
	border-radius: var(--border-radius);
	cursor: pointer;
	font-size: 0.9em;
	border: 1px solid #ccc;
	background: white;
}

button.primary {
	background: var(--primary-color);
	color: white;
	border-color: var(--primary-color);
}

button.primary:hover {
	background: var(--primary-hover);
}

button.secondary {
	background: white;
	color: var(--primary-color);
	border-color: var(--primary-color);
}

.new-row-form {
	margin-top: 16px;
	padding: 16px;
	border: 1px solid var(--primary-color);
	background-color: #f9f9f9;
	border-radius: var(--border-radius);
}

.new-row-form h3 {
	margin-bottom: 16px;
	color: var(--primary-color);
}

.form-field {
	margin-bottom: 12px;
}

.form-field label {
	display: block;
	font-weight: bold;
	margin-bottom: 4px;
}

.form-input {
	width: 100%;
	padding: 8px;
	border: 1px solid #ddd;
	border-radius: var(--border-radius);
}

.form-input[aria-invalid="true"] {
	border-color: var(--danger-color);
}

.error-message {
	color: var(--danger-color);
	font-size: 0.8em;
	margin-top: 4px;
	display: block;
}

.form-actions {
	display: flex;
	gap: 8px;
	margin-top: 16px;
}

.grid-tooltip {
	background: #333;
	color: white;
	padding: 4px 8px;
	border-radius: 4px;
	font-size: 12px;
	z-index: 100;
	pointer-events: none;
}

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
</style>
