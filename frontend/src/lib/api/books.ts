import { env } from '$env/dynamic/public';
import type { Book, BookFormData } from './types';

const BASE = () => env.PUBLIC_BOOKS_API;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
	const res = await fetch(`${BASE()}${path}`, {
		...init,
		headers: { 'Content-Type': 'application/json', ...init?.headers }
	});
	if (!res.ok) {
		const body = await res.json().catch(() => null);
		throw new Error(body?.detail ?? `Request failed: ${res.status}`);
	}
	if (res.status === 204) return undefined as T;
	return res.json();
}

export function listBooks(): Promise<Book[]> {
	return request('/books');
}

export function getBook(id: number): Promise<Book> {
	return request(`/books/${id}`);
}

export function createBook(data: BookFormData): Promise<Book> {
	return request('/books', { method: 'POST', body: JSON.stringify(data) });
}

export function updateBook(id: number, data: BookFormData): Promise<Book> {
	return request(`/books/${id}`, { method: 'PUT', body: JSON.stringify(data) });
}

export function deleteBook(id: number): Promise<void> {
	return request(`/books/${id}`, { method: 'DELETE' });
}
