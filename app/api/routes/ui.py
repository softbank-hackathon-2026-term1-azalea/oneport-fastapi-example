from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["ui"])

_INDEX = Path(__file__).resolve().parents[2] / "static" / "index.html"


@router.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(_INDEX, media_type="text/html")
