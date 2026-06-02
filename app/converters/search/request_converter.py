from pydantic import BaseModel

from app.gts.schemas.common.direction import GtsSearchRequest
from app.integrations.corendon.schemas.common.flight import FlightSearchBody, FlightItem
from app.integrations.corendon.schemas.common.passeger import PassengerType


def convert_search_request(gts: GtsSearchRequest) -> FlightSearchBody:
    
    dirs_count = len(gts.directions)
    if dirs_count == 1:
        trip_type = "1"
    elif dirs_count == 2:
        trip_type = "2"
    else:
        trip_type = "3"

    flights = [
        
        FlightItem(
            DeparturePointCode=d.departure,
            ArrivalPointCode=d.arrival,
            FlightDate=d.departure_date,
            DeparturePointType="0",
            ArrivalPointType="0",
        )
        for d in gts.directions
    ]

    return FlightSearchBody(
        TripType=trip_type,
        CurrencyCode=gts.currency,
        PassengerCounts=PassengerType(
            AdultCount=gts.adt,
            ChildCount=gts.chd,
            InfantCount=gts.inf,
        ),
        Flights=flights,
    )