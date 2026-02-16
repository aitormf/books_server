<script lang="ts">
	import type { Book, BookFormData } from '$lib/api/types';

	interface Props {
		book?: Book;
		onsave: (data: BookFormData) => void;
		oncancel: () => void;
	}

	let { book, onsave, oncancel }: Props = $props();

	let title = $state('');
	let isbn = $state('');
	let publication_year = $state('');

	$effect(() => {
		title = book?.title ?? '';
		isbn = book?.isbn ?? '';
		publication_year = book?.publication_year?.toString() ?? '';
	});

	function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		onsave({
			title,
			isbn: isbn || null,
			publication_year: publication_year ? parseInt(publication_year) : null
		});
	}
</script>

<form onsubmit={handleSubmit} class="bg-gray-50 border rounded-lg p-4 mb-4 space-y-3">
	<h3 class="font-semibold text-gray-700">{book ? 'Edit Book' : 'New Book'}</h3>

	<div class="grid grid-cols-1 md:grid-cols-3 gap-3">
		<div>
			<label for="title" class="block text-sm font-medium text-gray-600">Title *</label>
			<input
				id="title"
				type="text"
				bind:value={title}
				required
				maxlength="255"
				class="mt-1 w-full border rounded px-3 py-2 text-sm"
			/>
		</div>
		<div>
			<label for="isbn" class="block text-sm font-medium text-gray-600">ISBN</label>
			<input
				id="isbn"
				type="text"
				bind:value={isbn}
				maxlength="20"
				class="mt-1 w-full border rounded px-3 py-2 text-sm"
			/>
		</div>
		<div>
			<label for="publication_year" class="block text-sm font-medium text-gray-600">Publication Year</label>
			<input
				id="publication_year"
				type="number"
				bind:value={publication_year}
				class="mt-1 w-full border rounded px-3 py-2 text-sm"
			/>
		</div>
	</div>

	<div class="flex gap-2">
		<button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
			{book ? 'Update' : 'Create'}
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
