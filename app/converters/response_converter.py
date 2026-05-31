import hashlib
import secrets
from datetime import datetime
from typing import Any

from app.gts.schemas.common.airplane import AirplaneInfo
from app.gts.schemas.common.enums import PassengerType, TripType
from app.gts.schemas.common.price import PriceInfo, PriceDetail
from app.gts.schemas.common.refund import RefundReissue
from app.gts.schemas.common.route import Route
from app.gts.schemas.common.segment import Segment


def get_passenger_counts(data: dict[str, Any]) -> dict[str, int]:

    passenger = data.get("PassengerCounts", {})

    adt = passenger.get("AdultCount", 0)
    chd = passenger.get("ChildCount", 0)
    inf = passenger.get("InfantCount", 0)

    return {
        "ADT": adt,
        "CHD": chd,
        "INF": inf,
    }


def ms_to_minutes (ms : int) -> int :
    return ms // 60000 if ms else 0

def split_time ( dt_str : str) -> tuple[str ,str] :

     if  dt_str == ""  or dt_str is None:
         return "",""
     try:
         dt = datetime.fromisoformat(dt_str)
         return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
     except ValueError:
         return dt_str[:10], dt_str[11:16]






def  passanger_type_gts ( trip_type : int ) -> PassengerType:

    mapping = {1 : PassengerType.adult , 2 : PassengerType.child , 3 : PassengerType.infant }

    return  mapping.get(trip_type,PassengerType.adult)


def trip_type_gts ( trip_type : str ) ->  TripType:
    match trip_type:
        case "1":
            return TripType.one_way
        case "2":
            return TripType.round_trip
        case "3":
            return TripType.multi_city
        case _:
            raise ValueError(f"Неизвестный trip_type: {trip_type}")


def convert_segment (seg_data: dict[str, Any], seg_index: int) -> Segment:

    dep_date, dep_time = split_time(seg_data.get("DepartureDate", ""))
    arr_date, arr_time = split_time(seg_data.get("ArriveDate", ""))

    dep_code = seg_data.get("DepartureAirportCode", "")
    arr_code = seg_data.get("ArrivalAirportCode", "")
    leg = f"{dep_code}-{arr_code}"

    seg_key = hashlib.sha256(secrets.token_hex(8).encode()).hexdigest()

    return Segment(
        segment_index= seg_index,
        segment_key=seg_key,
        leg=leg,
        flight_number= seg_data.get("FlightNumber", ""),
        departure_country=seg_data.get("DepartureCityName", ""),  # страны нет → используем город
        departure_country_code=seg_data.get("DepartureCountryCode", ""),
        departure_city=seg_data.get("DepartureCityName", ""),
        departure_city_code=seg_data.get("DepartureCityCode", ""),
        departure_airport=seg_data.get("DepartureAirportName", ""),
        departure_airport_code=dep_code,
        departure_date=dep_date,
        departure_time=dep_time,
        departure_timezone="",

        arrival_country=seg_data.get("ArrivalCityName", ""),
        arrival_country_code=seg_data.get("ArriveCountryCode", ""),
        arrival_city=seg_data.get("ArrivalCityName", ""),
        arrival_city_code=seg_data.get("ArrivalCityCode", ""),
        arrival_airport=seg_data.get("ArrivalAirportName", ""),
        arrival_airport_code=arr_code,
        arrival_terminal="",
        arrival_date=arr_date,
        arrival_time=arr_time,
        arrival_timezone="",

        duration_minutes= ms_to_minutes(seg_data.get("TimeOnAir", 0)),
        stop_time_minutes=0,

        marketing_airline=seg_data.get("AirCraftType", ""),
        marketing_airline_code=seg_data.get("AirlineCode", ""),
        marketing_airline_logo="",
        operating_airline=seg_data.get("AirCraftType", ""),
        operating_airline_code=seg_data.get("AirlineCode", ""),
        operating_airline_logo="",

        seatmap_availability=False,
        services_availability=False,
        airplane_info=AirplaneInfo(
            airplane=seg_data.get("AirCraftType", ""),
            airplane_code=seg_data.get("AirCraftType", ""),
            seat_width="", seat_angle="",
            seat_scheme="", seat_distance="",
            has_wifi=False,
    ),
)

def convert_route( flight_key_data: dict[str, Any],   flight_route_data: dict[str, Any], route_index: int,) -> Route:
    dep_code =flight_key_data.get("DepartureAirportCode", "")
    arr_code =flight_key_data.get("ArrivalAirportCode", "")

    segments_raw = flight_route_data.get("Segments", [])
    segments = [convert_segment(seg , i + 1) for i, seg in enumerate(segments_raw)]

    route_index = route_index
    direction = f'{dep_code}-{arr_code}'
    stops = flight_route_data.get("Stops", 0)
    flight_time = ms_to_minutes(flight_route_data.get("TimeOnAir", 0))
    trip_time = ms_to_minutes(flight_route_data.get("TimeOnAir", 0)) or flight_time

    return Route(
        route_index=route_index,
        direction=direction,
        refundable=RefundReissue(status=None, type=None),
        reissue=RefundReissue(status=None, type=None),
        stops=max(0, len(segments) - 1),
        trip_time_minutes=trip_time,
        flight_time_minutes=flight_time,
        segments=segments,
    )




def convert_prices(
        fare_data: dict[str, Any],
        passenger_counts: dict[str, int],
) -> tuple[PriceInfo, list[PriceDetail]]:

    currency = fare_data.get("Currency", "EUR")
    sub_total = float(fare_data.get("SubTotal", 0))
    price_details: list[PriceDetail] = []

    quantity_map = {
        1: passenger_counts.get("ADT", 0),
        2: passenger_counts.get("CHD", 0),
        3: passenger_counts.get("INF", 0),
    }

    fare_list: list[dict] = fare_data.get("Fare", [])

    for fare in fare_list:
        traveller_type_int = fare.get("TravellerType", 1)
        quantity = quantity_map.get(traveller_type_int, 0)

        if quantity == 0:
            continue

        passenger_type = passanger_type_gts(traveller_type_int)
        base = float(fare.get("BasePrice", 0))
        tax = float(fare.get("TaxPrice", 0))
        discount = float(fare.get("DiscountPrice", 0))
        price = float(fare.get("Price", 0))
        service_charge = float(fare.get("ServiceCharge", 0))

        detail = PriceDetail(
            passenger_type=passenger_type,
            currency=currency,
            quantity=quantity,
            single_base_amount=base,
            single_tax_amount=tax,
            single_tax_details=[],
            fee_amount=0.0,
            to_commission_amount=0.0,
            commission_amount=abs(discount),
            single_total_amount=price,
            base_total_amount=base * quantity,
            tax_total_amount=tax * quantity,
            total_amount=price * quantity,
            payable_amount=price * quantity,
            single_fee_amount=0.0,
            single_service_fee_amount=service_charge,
            single_commission_amount=abs(discount),
            single_from_commission_amount=0.0,
            single_to_commission_amount=0.0,
            single_payable_amount=price,
            service_fee_amount=service_charge * quantity,
            from_commission_amount=0.0,
            profit_commission_amount=0.0,
        )
        price_details.append(detail)

    price_info = PriceInfo(
        price=sub_total,
        currency=currency,
        fee_amount=0.0,
        base_amount=float(fare_data.get("BaseTotal", sub_total)),
        commission_amount=0.0,
        from_commission_amount=0.0,
        to_commission_amount=0.0,
    )

    return price_info, price_details