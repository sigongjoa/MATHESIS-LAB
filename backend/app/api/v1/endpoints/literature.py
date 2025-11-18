import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.schemas.literature_item import (
    LiteratureItemSchema,
    LiteratureItemCreate,
    LiteratureItemUpdate,
    ZoteroItemResponse, # Added ZoteroItemResponse
)
from backend.app.services.literature_service import LiteratureService
from backend.app.services.zotero_service import zotero_service # Added zotero_service

router = APIRouter()

def get_literature_service(db: Session = Depends(get_db)) -> LiteratureService:
    return LiteratureService(db)

@router.post("/", response_model=LiteratureItemSchema, status_code=201)
def create_literature_item(
    item_in: LiteratureItemCreate,
    service: LiteratureService = Depends(get_literature_service),
):
    """
    Create new literature item.
    """
    return service.create(item_in=item_in)

@router.get("/", response_model=List[LiteratureItemSchema])
def read_literature_items(
    tags: Optional[str] = Query(None, description="Comma-separated tags to search for"),
    match: str = Query("all", enum=["all", "any"], description="Match all or any of the tags"),
    skip: int = 0,
    limit: int = 100,
    service: LiteratureService = Depends(get_literature_service),
):
    """
    Retrieve literature items. Can be filtered by tags.
    """
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        items = service.get_multi_by_tags(tags=tag_list, match=match, skip=skip, limit=limit)
    else:
        items = service.get_multi(skip=skip, limit=limit)
    return items

@router.get("/{item_id}", response_model=LiteratureItemSchema)
def read_literature_item(
    item_id: uuid.UUID,
    service: LiteratureService = Depends(get_literature_service),
):
    """
    Get a specific literature item by ID.
    """
    db_item = service.get(item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Literature item not found")
    return db_item

@router.put("/{item_id}", response_model=LiteratureItemSchema)
def update_literature_item(
    item_id: uuid.UUID,
    item_in: LiteratureItemUpdate,
    service: LiteratureService = Depends(get_literature_service),
):
    """
    Update a literature item.
    """
    db_item = service.update(item_id=item_id, item_in=item_in)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Literature item not found")
    return db_item

@router.delete("/{item_id}", response_model=LiteratureItemSchema)
def delete_literature_item(
    item_id: uuid.UUID,
    service: LiteratureService = Depends(get_literature_service),
):
    """
    Delete a literature item.
    """
    db_item = service.delete(item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Literature item not found")
    return db_item

@router.get("/zotero/items", response_model=List[ZoteroItemResponse])
async def search_zotero_items(
    tag: str = Query(..., description="Tag to search for in Zotero items"),
):
    """
    Search for Zotero literature items by tag from the external Zotero API.
    """
    items = await zotero_service.get_items_by_tag(tag=tag)
    return items
