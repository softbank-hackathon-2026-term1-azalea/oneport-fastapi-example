from pydantic import BaseModel


class VisitCount(BaseModel):
    visits: int
