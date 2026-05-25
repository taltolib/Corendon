from typing import List
from pydantic import BaseModel

from app.gts.schemas.common.enums import PassengerType
from app.integrations.corendon.schemas.common.passeger import Passenger


class FlightItem(BaseModel):
    DeparturePointCode: str
    FlightDate: str
    ArrivalPointCode: str
    DeparturePointType: str
    ArrivalPointType: str

class FlightSearchBody(BaseModel):
    TripType: str
    PassengerCounts: PassengerType
    CurrencyCode: str
    Flights: List[FlightItem]


class FlightPriceBody(BaseModel):
    TripType: str
    CurrencyCode: str
    PassengerCounts: PassengerType
    FlightKeys: list[str]

class FlightBookBody(BaseModel):
    Passengers: List[Passenger]
    TripType: str
    PassengerCounts: PassengerType
    CurrencyCode: str
    FlightKeys: List[str]