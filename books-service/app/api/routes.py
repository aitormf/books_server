from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.schemas import (
    AssignAuthorsRequest,
    BookCreate,
    BookResponse,
    BookUpdate,
)
from app.dependencies import get_book_service
from app.domain.entities import Book
from app.domain.services import BookService

router = APIRouter(prefix="/books", tags=["books"])


@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    book_data: BookCreate,
    request: Request,
    service: BookService = Depends(get_book_service),
) -> BookResponse:
    """Create a new book."""
    book = Book(
        id=None,
        title=book_data.title,
        isbn=book_data.isbn,
        publication_year=book_data.publication_year,
    )
    correlation_id = getattr(request.state, "correlation_id", None)
    try:
        created = await service.create_book(book, correlation_id=correlation_id)
        return BookResponse.from_entity(created)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[BookResponse])
async def list_books(
    skip: int = 0,
    limit: int = 100,
    service: BookService = Depends(get_book_service),
) -> List[BookResponse]:
    """List all books with pagination."""
    books = await service.get_all_books(skip=skip, limit=limit)
    return [BookResponse.from_entity(b) for b in books]


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: int,
    service: BookService = Depends(get_book_service),
) -> BookResponse:
    """Get a book by ID with its authors."""
    book = await service.get_book_with_authors(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return BookResponse.from_entity(book)


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: int,
    book_data: BookUpdate,
    request: Request,
    service: BookService = Depends(get_book_service),
) -> BookResponse:
    """Update an existing book."""
    book = Book(
        id=book_id,
        title=book_data.title,
        isbn=book_data.isbn,
        publication_year=book_data.publication_year,
    )
    correlation_id = getattr(request.state, "correlation_id", None)
    try:
        updated = await service.update_book(
            book_id, book, correlation_id=correlation_id
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Book not found")
        return BookResponse.from_entity(updated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: int,
    request: Request,
    service: BookService = Depends(get_book_service),
) -> None:
    """Delete a book."""
    correlation_id = getattr(request.state, "correlation_id", None)
    deleted = await service.delete_book(book_id, correlation_id=correlation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Book not found")


@router.post("/{book_id}/authors", status_code=status.HTTP_200_OK)
async def assign_authors(
    book_id: int,
    request_data: AssignAuthorsRequest,
    request: Request,
    service: BookService = Depends(get_book_service),
) -> dict:
    """Assign authors to a book."""
    correlation_id = getattr(request.state, "correlation_id", None)
    try:
        await service.assign_authors_to_book(
            book_id, request_data.author_ids, correlation_id=correlation_id
        )
        return {"message": "Authors assigned successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/{book_id}/authors/{author_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def unassign_author(
    book_id: int,
    author_id: int,
    request: Request,
    service: BookService = Depends(get_book_service),
) -> None:
    """Remove an author from a book."""
    correlation_id = getattr(request.state, "correlation_id", None)
    try:
        await service.unassign_author_from_book(
            book_id, author_id, correlation_id=correlation_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
