from fastapi import APIRouter, Query, status

from app.api.deps import SessionDep
from app.notes import service
from app.notes.schemas import NoteCreate, NoteRead, NoteUpdate

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("")
async def list_notes(
    session: SessionDep, limit: int = Query(default=50, ge=1, le=200)
) -> list[NoteRead]:
    notes = await service.list_notes(session, limit=limit)
    return [NoteRead.model_validate(note) for note in notes]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_note(session: SessionDep, payload: NoteCreate) -> NoteRead:
    note = await service.create_note(session, payload)
    return NoteRead.model_validate(note)


@router.patch("/{note_id}")
async def update_note(session: SessionDep, note_id: int, payload: NoteUpdate) -> NoteRead:
    note = await service.update_note(session, note_id, payload)
    return NoteRead.model_validate(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(session: SessionDep, note_id: int) -> None:
    await service.delete_note(session, note_id)
