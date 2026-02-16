from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.schemas import (
    AssignBooksRequest,
    AuthorCreate,
    AuthorResponse,
    AuthorUpdate,
)
from app.dependencies import get_author_service
from app.domain.entities import Author
from app.domain.services import AuthorService

router = APIRouter(prefix="/authors", tags=["authors"])


@router.post("", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
async def create_author(
    author_data: AuthorCreate,
    request: Request,
    service: AuthorService = Depends(get_author_service),
) -> AuthorResponse:
    """Create a new author."""
    author = Author(
        id=None,
        name=author_data.name,
        birth_date=author_data.birth_date,
        nationality=author_data.nationality,
    )
    correlation_id = getattr(request.state, "correlation_id", None)
    try:
        created = await service.create_author(author, correlation_id=correlation_id)
        return AuthorResponse.from_entity(created)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[AuthorResponse])
async def list_authors(
    skip: int = 0,
    limit: int = 100,
    service: AuthorService = Depends(get_author_service),
) -> List[AuthorResponse]:
    """List all authors with pagination."""
    authors = await service.get_all_authors(skip=skip, limit=limit)
    return [AuthorResponse.from_entity(a) for a in authors]


@router.get("/{author_id}", response_model=AuthorResponse)
async def get_author(
    author_id: int,
    service: AuthorService = Depends(get_author_service),
) -> AuthorResponse:
    """Get an author by ID with their books."""
    author = await service.get_author_with_books(author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return AuthorResponse.from_entity(author)


@router.put("/{author_id}", response_model=AuthorResponse)
async def update_author(
    author_id: int,
    author_data: AuthorUpdate,
    request: Request,
    service: AuthorService = Depends(get_author_service),
) -> AuthorResponse:
    """Update an existing author."""
    author = Author(
        id=author_id,
        name=author_data.name,
        birth_date=author_data.birth_date,
        nationality=author_data.nationality,
    )
    correlation_id = getattr(request.state, "correlation_id", None)
    try:
        updated = await service.update_author(
            author_id, author, correlation_id=correlation_id
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Author not found")
        return AuthorResponse.from_entity(updated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_author(
    author_id: int,
    request: Request,
    service: AuthorService = Depends(get_author_service),
) -> None:
    """Delete an author."""
    correlation_id = getattr(request.state, "correlation_id", None)
    deleted = await service.delete_author(author_id, correlation_id=correlation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Author not found")


@router.post("/{author_id}/books", status_code=status.HTTP_200_OK)
async def assign_books(
    author_id: int,
    request_data: AssignBooksRequest,
    request: Request,
    service: AuthorService = Depends(get_author_service),
) -> dict:
    """Assign books to an author."""
    correlation_id = getattr(request.state, "correlation_id", None)
    try:
        await service.assign_books_to_author(
            author_id, request_data.book_ids, correlation_id=correlation_id
        )
        return {"message": "Books assigned successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/{author_id}/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def unassign_book(
    author_id: int,
    book_id: int,
    request: Request,
    service: AuthorService = Depends(get_author_service),
) -> None:
    """Remove a book from an author."""
    correlation_id = getattr(request.state, "correlation_id", None)
    try:
        await service.unassign_book_from_author(
            author_id, book_id, correlation_id=correlation_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
