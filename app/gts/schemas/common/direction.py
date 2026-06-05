from pydantic import BaseModel, Field


class GtsDirection(BaseModel):
    departure: str
    arrival: str
    departure_date: str

class GtsSearchRequest(BaseModel):
    directions: list[GtsDirection]
    adt: int
    chd: int
    inf: int
    ins: int = 0
    currency: str = "USD"
    cabin_class: str = Field(default="", )
    flexible: bool = False
    direct: bool = False
    airlines: list[str] = []
    passengers_ids: list = []