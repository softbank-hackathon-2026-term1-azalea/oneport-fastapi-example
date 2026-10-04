from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.notes.exceptions import NoteNotFoundError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NoteNotFoundError)
    async def note_not_found(_: Request, exc: NoteNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc), "note_id": exc.note_id},
        )
