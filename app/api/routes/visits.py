from fastapi import APIRouter

from app.api.deps import CacheDep
from app.visits import service
from app.visits.schemas import VisitCount

router = APIRouter(prefix="/visits", tags=["visits"])


@router.get("")
async def get_visits(cache: CacheDep) -> VisitCount:
    return VisitCount(visits=await service.count_visits(cache))


@router.post("")
async def record_visit(cache: CacheDep) -> VisitCount:
    return VisitCount(visits=await service.record_visit(cache))
