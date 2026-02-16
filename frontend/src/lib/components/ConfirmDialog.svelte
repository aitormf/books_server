<script lang="ts">
	interface Props {
		open: boolean;
		message: string;
		onconfirm: () => void;
		oncancel: () => void;
	}

	let { open, message, onconfirm, oncancel }: Props = $props();
</script>

{#if open}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
		onkeydown={(e) => e.key === 'Escape' && oncancel()}
	>
		<div class="bg-white rounded-lg shadow-lg p-6 max-w-sm w-full mx-4">
			<p class="text-gray-800 mb-6">{message}</p>
			<div class="flex justify-end gap-3">
				<button
					class="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
					onclick={oncancel}
				>
					Cancel
				</button>
				<button
					class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
					onclick={onconfirm}
				>
					Delete
				</button>
			</div>
		</div>
	</div>
{/if}
