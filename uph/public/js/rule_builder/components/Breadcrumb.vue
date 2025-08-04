<template>
	<div class="breadcrumb-container" :class="{ clickable: clickable }">
		<template v-for="(item, i) in processedItems" :key="getItemKey(item, i)">
			<!-- Item Content with Remove Button -->
			<div class="breadcrumb-item-wrapper">
				<div class="breadcrumb-item" :class="itemClasses(item, i)">
					<component
						:is="clickable && !isDisabled(item) ? 'button' : 'span'"
						class="breadcrumb-content"
						@click="handleClick(item, i)"
					>
						<slot name="item" :item="item" :index="i">
							{{ __(item.label) || __(item.value) || __(item.fieldname) || __(item.name) || item }}
						</slot>
					</component>
				</div>

				<!-- Remove Button for Each Item when showRemove='all' -->
				<button
					v-if="showRemove === 'all'"
					class="breadcrumb-remove"
					@click.stop="handleRemove(i)"
					:disabled="isRemoveDisabled(item, i)"
				>
					<slot name="remove-icon">×</slot>
				</button>
			</div>

			<!-- Separator -->
			<div v-if="i < processedItems.length - 1" class="breadcrumb-separator">
				<slot name="separator">{{ separator }}</slot>
			</div>
		</template>

		<!-- Single Remove Button when showRemove='last' -->
		<button
			v-if="showRemove === 'last' && processedItems.length > 0"
			class="breadcrumb-remove"
			@click.stop="handleRemove(processedItems.length - 1)"
			:disabled="
				isRemoveDisabled(processedItems[processedItems.length - 1], processedItems.length - 1)
			"
		>
			<slot name="remove-icon">×</slot>
		</button>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	items: {
		type: Array,
		default: () => [],
		validator: (value) => {
			return value.every(
				(item) => typeof item === "object" || typeof item === "string" || typeof item === "number",
			);
		},
	},
	separator: {
		type: String,
		default: "›",
	},
	clickable: {
		type: [Boolean, Function],
		default: false,
	},
	disabled: {
		type: Boolean,
		default: false,
	},
	showRemove: {
		type: String,
		default: "last",
		validator: (value) => ["all", "last", "none"].includes(value),
	},
	removeDisabled: {
		type: [Boolean, Function],
		default: false,
	},
	itemClass: {
		type: [String, Function],
		default: "",
	},
	activeClass: {
		type: String,
		default: "text-blue-600 font-medium",
	},
	inactiveClass: {
		type: String,
		default: "text-gray-600",
	},
});

const emit = defineEmits(["item-click", "remove", "update:items"]);

const processedItems = computed(() => {
	return props.items.map((item, index) => {
		if (typeof item === "object") {
			return {
				...item,
				__index: index,
				__disabled: item.disabled || false,
			};
		}
		return {
			label: String(item),
			value: item,
			__index: index,
			__disabled: false,
		};
	});
});

function getItemKey(item, index) {
	return item.id || item.key || `${index}-${JSON.stringify(item)}`;
}

function isDisabled(item) {
	return props.disabled || item.__disabled;
}

function isRemoveDisabled(item, index) {
	if (typeof props.removeDisabled === "function") {
		return props.removeDisabled(item, index);
	}
	return props.removeDisabled || isDisabled(item);
}

function itemClasses(item, index) {
	const classes = [];

	if (typeof props.itemClass === "function") {
		classes.push(props.itemClass(item, index));
	} else {
		classes.push(props.itemClass);
	}

	if (index === processedItems.value.length - 1) {
		classes.push(props.activeClass);
	} else {
		classes.push(props.inactiveClass);
	}

	if (props.clickable && !isDisabled(item)) {
		classes.push("hover:underline cursor-pointer");
	}

	return classes.filter(Boolean).join(" ");
}

function handleClick(item, index) {
	if (!props.clickable || isDisabled(item)) return;
	emit("item-click", { item, index });
}

function handleRemove(index) {
	const item = processedItems.value[index];
	if (isRemoveDisabled(item, index)) return;

	const newItems = [...props.items];
	newItems.splice(index, 1);

	emit("update:items", newItems);
	emit("remove", {
		item,
		index,
		remainingItems: newItems,
	});
}
</script>

<style scoped>
.breadcrumb-container {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	gap: 0.5rem;
}

.breadcrumb-item-wrapper {
	display: flex;
	align-items: center;
	gap: 0.25rem;
}

.breadcrumb-item {
	display: inline-flex;
	align-items: center;
	transition: color 0.2s ease;
}

.breadcrumb-content {
	background: none;
	border: none;
	padding: 0;
	font: inherit;
	text-align: left;
}

.breadcrumb-separator {
	color: var(--separator-color, #9ca3af);
	user-select: none;
}

.breadcrumb-remove {
	background: none;
	border: none;
	color: #ef4444;
	cursor: pointer;
	font-weight: bold;
	padding: 0 0.1rem;
	opacity: 0.7;
	transition: opacity 0.2s;
}

.breadcrumb-remove:hover {
	opacity: 1;
}

.breadcrumb-remove:disabled {
	opacity: 0.3;
	cursor: not-allowed;
}

.clickable .breadcrumb-item:not(.disabled):hover {
	text-decoration: underline;
}
</style>
