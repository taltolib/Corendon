from app.integrations.corendon.schemas.common.flight import FlightPriceBody
from app.integrations.corendon.schemas.common.passeger import PassengerType


def build_verify_request ( meta : dict ) -> FlightPriceBody :

    trip_type = meta.get("trip_type", "1")
    all_keys  = meta.get("flight_keys", [])
    offer_id  = meta.get("offer_id", "")
    currency  = meta.get("currency", "USD")

    passenger_counts = PassengerType(
        AdultCount  = meta.get("adt", 1),
        ChildCount  = meta.get("chd", 0),
        InfantCount = meta.get("inf", 0),
    )

    if trip_type == "1" :

        flight_keys = [offer_id]

    else :
        remaining   = [i for i in all_keys if i != offer_id]
        ret_key     = remaining[0] if remaining else ""
        flight_keys = [offer_id, ret_key] if ret_key else [offer_id]

    return FlightPriceBody(
        TripType        = trip_type,
        CurrencyCode    = currency,
        PassengerCounts = passenger_counts,
        FlightKeys      = flight_keys,
    )
