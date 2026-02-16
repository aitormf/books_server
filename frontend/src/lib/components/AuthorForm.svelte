<script lang="ts">
	import type { Author, AuthorFormData } from '$lib/api/types';

	interface Props {
		author?: Author;
		onsave: (data: AuthorFormData) => void;
		oncancel: () => void;
	}

	let { author, onsave, oncancel }: Props = $props();

	let name = $state('');
	let birth_date = $state('');
	let nationality = $state('');

	$effect(() => {
		name = author?.name ?? '';
		birth_date = author?.birth_date ?? '';
		nationality = author?.nationality ?? '';
	});

	function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		onsave({
			name,
			birth_date: birth_date || null,
			nationality: nationality || null
		});
	}
</script>

<form onsubmit={handleSubmit} class="bg-gray-50 border rounded-lg p-4 mb-4 space-y-3">
	<h3 class="font-semibold text-gray-700">{author ? 'Edit Author' : 'New Author'}</h3>

	<div class="grid grid-cols-1 md:grid-cols-3 gap-3">
		<div>
			<label for="name" class="block text-sm font-medium text-gray-600">Name *</label>
			<input
				id="name"
				type="text"
				bind:value={name}
				required
				maxlength="255"
				class="mt-1 w-full border rounded px-3 py-2 text-sm"
			/>
		</div>
		<div>
			<label for="birth_date" class="block text-sm font-medium text-gray-600">Birth Date</label>
			<input
				id="birth_date"
				type="date"
				bind:value={birth_date}
				class="mt-1 w-full border rounded px-3 py-2 text-sm"
			/>
		</div>
		<div>
			<label for="nationality" class="block text-sm font-medium text-gray-600">Nationality</label>
			<input
				id="nationality"
				type="text"
				bind:value={nationality}
				maxlength="100"
				class="mt-1 w-full border rounded px-3 py-2 text-sm"
			/>
		</div>
	</div>

	<div class="flex gap-2">
		<button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
			{author ? 'Update' : 'Create'}
		</button>
		<button
			type="button"
			class="px-4 py-2 border border-gray-300 rounded text-sm hover:bg-gray-50"
			onclick={oncancel}
		>
			Cancel
		</button>
	</div>
</form>
