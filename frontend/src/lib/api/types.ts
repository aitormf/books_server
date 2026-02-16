export interface AuthorSummary {
	id: number;
	name: string;
	nationality: string | null;
}

export interface BookSummary {
	id: number;
	title: string;
	isbn: string | null;
	publication_year: number | null;
}

export interface Author {
	id: number;
	name: string;
	birth_date: string | null;
	nationality: string | null;
	created_at: string | null;
	updated_at: string | null;
	books: BookSummary[];
}

export interface Book {
	id: number;
	title: string;
	isbn: string | null;
	publication_year: number | null;
	created_at: string | null;
	updated_at: string | null;
	authors: AuthorSummary[];
}

export interface AuthorFormData {
	name: string;
	birth_date: string | null;
	nationality: string | null;
}

export interface BookFormData {
	title: string;
	isbn: string | null;
	publication_year: number | null;
}
