<script lang="ts">
	import { listBooks, createBook, updateBook, deleteBook } from '$lib/api/books';
	import type { Book, BookFormData } from '$lib/api/types';
	import BookForm from '$lib/components/BookForm.svelte';
	import ConfirmDialog from '$lib/components/ConfirmDialog.svelte';

	let books = $state<Book[]>([]);
	let loading = $state(true);
	let error = $state('');
	let showForm = $state(false);
	let editingId = $state<number | null>(null);
	let deleteTarget = $state<Book | null>(null);

	let editingBook = $derived(editingId ? books.find((b) => b.id === editingId) : undefined);

	async function load() {
		loading = true;
		error = '';
		try {
			books = await listBooks();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load books';
		} finally {
			loading = false;
		}
	}

	async function handleSave(data: BookFormData) {
		try {
			if (editingId) {
				await updateBook(editingId, data);
			} else {
				await createBook(data);
			}
			showForm = false;
			editingId = null;
			await load();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to save book';
		}
	}

	async function handleDelete() {
		if (!deleteTarget) return;
		try {
			await deleteBook(deleteTarget.id);
			deleteTarget = null;
			await load();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to delete book';
		}
	}

	function startEdit(book: Book) {
		editingId = book.id;
		showForm = true;
	}

	function startCreate() {
		editingId = null;
		showForm = true;
	}

	function cancelForm() {
		showForm = false;
		editingId = null;
	}

	$effect(() => {
		load();
	});
</script>

<div class="space-y-4">
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-bold text-gray-800">Books</h1>
		{#if !showForm}
			<button
				class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
				onclick={startCreate}
			>
				+ New Book
			</button>
		{/if}
	</div>

	{#if error}
		<div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
			{error}
			<button class="ml-2 underline" onclick={() => (error = '')}>dismiss</button>
		</div>
	{/if}

	{#if showForm}
		<BookForm book={editingBook} onsave={handleSave} oncancel={cancelForm} />
	{/if}

	{#if loading}
		<p class="text-gray-500">Loading...</p>
	{:else if books.length === 0}
		<p class="text-gray-500">No books found.</p>
	{:else}
		<div class="overflow-x-auto bg-white rounded-lg shadow">
			<table class="w-full text-sm text-left">
				<thead class="bg-gray-50 text-gray-600 uppercase text-xs">
					<tr>
						<th class="px-4 py-3">Title</th>
						<th class="px-4 py-3">ISBN</th>
						<th class="px-4 py-3">Year</th>
						<th class="px-4 py-3">Authors</th>
						<th class="px-4 py-3 text-right">Actions</th>
					</tr>
				</thead>
				<tbody class="divide-y">
					{#each books as book (book.id)}
						<tr class="hover:bg-gray-50">
							<td class="px-4 py-3 font-medium text-gray-900">{book.title}</td>
							<td class="px-4 py-3 text-gray-600">{book.isbn ?? '-'}</td>
							<td class="px-4 py-3 text-gray-600">{book.publication_year ?? '-'}</td>
							<td class="px-4 py-3 text-gray-600">{book.authors.length}</td>
							<td class="px-4 py-3 text-right space-x-2">
								<button
									class="text-blue-600 hover:underline text-sm"
									onclick={() => startEdit(book)}
								>
									Edit
								</button>
								<button
									class="text-red-600 hover:underline text-sm"
									onclick={() => (deleteTarget = book)}
								>
									Delete
								</button>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>

<ConfirmDialog
	open={deleteTarget !== null}
	message="Are you sure you want to delete book '{deleteTarget?.title}'?"
	onconfirm={handleDelete}
	oncancel={() => (deleteTarget = null)}
/>
