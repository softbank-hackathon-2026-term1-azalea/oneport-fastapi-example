import logging
from collections.abc import Sequence

from sqlalchemy import delete, select

from app.core.db import AsyncSession
from app.notes.exceptions import NoteNotFoundError
from app.notes.models import Note
from app.notes.schemas import NoteCreate, NoteUpdate

log = logging.getLogger(__name__)


async def list_notes(session: AsyncSession, *, limit: int) -> Sequence[Note]:
    result = await session.scalars(
        select(Note).order_by(Note.created_at.desc(), Note.id.desc()).limit(limit)
    )
    return result.all()


async def create_note(session: AsyncSession, data: NoteCreate) -> Note:
    note = Note(title=data.title)
    session.add(note)
    await session.commit()
    await session.refresh(note)
    log.info("note created", extra={"note_id": note.id})
    return note


async def update_note(session: AsyncSession, note_id: int, data: NoteUpdate) -> Note:
    note = await session.get(Note, note_id)
    if note is None:
        raise NoteNotFoundError(note_id)
    note.done = data.done
    await session.commit()
    log.info("note updated", extra={"note_id": note_id, "done": data.done})
    return note


async def delete_note(session: AsyncSession, note_id: int) -> None:
    deleted_id = await session.scalar(delete(Note).where(Note.id == note_id).returning(Note.id))
    if deleted_id is None:
        raise NoteNotFoundError(note_id)
    await session.commit()
    log.info("note deleted", extra={"note_id": note_id})
