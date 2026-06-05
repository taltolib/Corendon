import hashlib
import secrets
import uuid
from datetime import datetime
from typing import Any

from app.gts.schemas.common.airplane import AirplaneInfo
from app.gts.schemas.common.enums import PassengerType, TripType
from app.gts.schemas.common.baggage import BaggageInfo, BaggageAllowance, HandBaggage, BaggageSize
from app.gts.schemas.common.fare import FareInfo
from app.gts.schemas.common.price import PriceInfo, PriceDetail
from app.gts.schemas.common.provider import Provider, SupplierProvider
from app.gts.schemas.common.refund import RefundReissue
from app.gts.schemas.common.route import Route
from app.gts.schemas.common.segment import Segment
from app.gts.schemas.common.upsell import Upsell
from app.gts.schemas.offer import Offer


def get_passenger_counts(data: dict[str, Any]) -> dict[str, int]:

    passenger = data.get("PassengerCounts") or {}

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


def convert_segment (seg_data: dict[str, Any], seg_index: int, route_data: dict[str, Any]) -> Segment:

    dep_date, dep_time = split_time(seg_data.get("DepartureDate", ""))
    arr_date, arr_time = split_time(seg_data.get("ArriveDate", ""))

    dep_code = route_data.get("DepartureAirportCode", "")
    arr_code = route_data.get("ArrivalAirportCode", "")

    departure_c_code = route_data.get("DepartureCountryCode", "")
    arrival_c_code = route_data.get("ArriveCountryCode", "")

    leg = f"{dep_code}-{arr_code}"

    seg_key = hashlib.sha256(secrets.token_hex(8).encode()).hexdigest() #Хозир генерацияни узим килябман

    return Segment(
        segment_index= seg_index,
        segment_key=seg_key,
        leg=leg,
        flight_number= seg_data.get("FlightNumber", ""),
        departure_country=seg_data.get("DepartureCityName", ""),
        departure_country_code= departure_c_code,
        departure_city=seg_data.get("DepartureCityName", ""),
        departure_city_code=seg_data.get("DepartureCityCode", ""),
        departure_airport=seg_data.get("DepartureAirportName", ""),
        departure_airport_code=dep_code,
        departure_date=dep_date,
        departure_time=dep_time,
        departure_timezone="",

        arrival_country=seg_data.get("ArrivalCityName", ""),
        arrival_country_code=arrival_c_code,
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
            airplane=seg_data.get("AirCraftType", ""),#
            airplane_code=seg_data.get("AirCraftType", ""), #
            seat_width="", seat_angle="",
            seat_scheme="", seat_distance="",
            has_wifi=False,
    ),
)

def convert_route(flight_route_data: dict[str, Any], route_index: int) -> Route:
    dep_code = flight_route_data.get("DepartureAirportCode", "")
    arr_code = flight_route_data.get("ArrivalAirportCode", "")

    segments_raw = flight_route_data.get("Segments", [])
    segments = [
        convert_segment(seg, i + 1, flight_route_data)
        for i, seg in enumerate(segments_raw)
    ]

    direction = f'{dep_code}-{arr_code}'
    flight_time = ms_to_minutes(flight_route_data.get("TimeOnAir", 0))

    return Route(
        route_index=route_index,
        direction=direction,
        refundable=RefundReissue(status=None, type=None),
        reissue=RefundReissue(status=None, type=None),
        stops = len(segments) - 1 if len(segments) > 0 else 0,
        trip_time_minutes=flight_time,
        flight_time_minutes=flight_time,
        segments=segments,
    )




def convert_prices(
        fare_data: dict[str, Any],
        passenger_counts: dict[str, int],
        currency: str = "EUR",
) -> tuple[PriceInfo, list[PriceDetail]]:
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
        base = fare.get("BasePrice", 0)
        tax = fare.get("TaxPrice", 0)
        discount = fare.get("DiscountPrice", 0)
        price = fare.get("Price", 0)
        service_charge = fare.get("ServiceCharge", 0)

        detail = PriceDetail(
            passenger_type=passenger_type,
            currency=currency,
            quantity=quantity,
            single_base_amount=base,
            single_tax_amount=tax,
            single_tax_details= 0.0,
            fee_amount=0.0,
            to_commission_amount=0.0,
            commission_amount=abs(discount),
            single_total_amount=base + tax,
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
        base_amount = fare_data.get("BaseTotal", sub_total),
        commission_amount=0.0,
        from_commission_amount=0.0,
        to_commission_amount=0.0,
    )

    return price_info, price_details

def convert_fares_info(
        fare_data: dict[str, Any],
        segment_keys: list[str],
        legs: list[str],
        passenger_counts: dict[str, int],
) -> list[FareInfo]:

    quantity_map = {
        1: passenger_counts.get("ADT", 0),
        2: passenger_counts.get("CHD", 0),
        3: passenger_counts.get("INF", 0),
    }

    fare_list= fare_data.get("Fare", [])
    fares = []

    for fare in fare_list:
        traveller_type_int = fare.get("TravellerType", 1)
        quantity = quantity_map.get(traveller_type_int, 0)

        if quantity == 0:
            continue

        passenger_type = passanger_type_gts(traveller_type_int)

        fares.append(
            FareInfo(
            segment_keys=segment_keys,
            leg=legs,
            passenger_type=passenger_type,
            seats=fare_data.get("RestPax", 0),
            upsell=Upsell(
                name="PUBLISHED",
                services=fare_data.get("AirFareRules", []),
            ),
            fare_code=fare_data.get("FareBasisCode", ""),
            service_class=fare_data.get("AirFareName", ""),
            service_class_code=fare_data.get("AirFareCode", ""),
            booking_class=fare_data.get("PriceBandCode", ""),
            description="",
        ))

    return fares


def convert_baggages_info(
        fare_data: dict[str, Any],
        segment_keys: list[str],
        legs: list[str],
        passenger_counts: dict[str, int],
) -> list[BaggageInfo]:

    quantity_map = {
        1: passenger_counts.get("ADT", 0),
        2: passenger_counts.get("CHD", 0),
        3: passenger_counts.get("INF", 0),
    }

    baggage_kg = fare_data.get("Baggage", 0)
    hand_luggage_kg =fare_data.get("HandLuggage", 0)
    infant_baggage_kg = fare_data.get("InfantBaggage", 0)

    fare_list= fare_data.get("Fare", [])
    baggages: list[BaggageInfo] = []

    empty_size = BaggageSize(height=None, width=None, length=None, unit="")

    for fare in fare_list:
        traveller_type_int = fare.get("TravellerType", 1)
        quantity = quantity_map.get(traveller_type_int, 0)

        if quantity == 0:
            continue

        passenger_type = passanger_type_gts(traveller_type_int)

        if traveller_type_int == 3:
            bag_value = infant_baggage_kg
        else:
            bag_value = baggage_kg

        baggages.append(BaggageInfo(
            segment_keys=segment_keys,
            leg=legs,
            passenger_type=passenger_type,
            baggage=BaggageAllowance(
                value=bag_value,
                unit="kg",
                size=empty_size,
            ),
            hand_baggage=HandBaggage(
                value=1,
                unit="pc",
                weight=hand_luggage_kg,
                size=empty_size,
            ),
            description="",
        ))

    return baggages


def convert_search_response(corendon_res: dict) -> list[Offer]:
    offers = []
    passenger_counts = get_passenger_counts(corendon_res)
    currency = corendon_res.get("Currency", "EUR")
    flights_data = corendon_res.get("Flights", [])

    directions = []
    for route_index, flight_group in enumerate(flights_data):

        routes_with_fares = []

        for route_variant in flight_group.get("Value", []):

            route = convert_route(
                flight_route_data=route_variant.get("Key", {}),
                route_index=route_index + 1,
            )

            fare_variants = route_variant.get("Value", [])

            routes_with_fares.append((route, fare_variants))

        directions.append(routes_with_fares)

    if not directions:
        return offers

    if len(directions) == 1:
        for route, fare_variants in directions[0]:

            routes = [route]

            segment_keys = []

            for seg in route.segments:
                segment_keys.append(seg.segment_key)

            legs = []

            for leg in route.segments:
                legs.append(leg.leg)

            has_upsell = len(fare_variants) > 1

            for fare_data in fare_variants:
                price_info, price_details = convert_prices(fare_data, passenger_counts, currency)
                fares_info = convert_fares_info(fare_data, segment_keys, legs, passenger_counts)
                baggages_info = convert_baggages_info(fare_data, segment_keys, legs, passenger_counts)
                print(price_info, "ответ price_info ⬇️")

                offer = Offer(
                    offer_id=fare_data.get("FlightKey", str(uuid.uuid4())),
                    price_info=price_info,
                    reprice_available=True,
                    upsell=has_upsell,
                    booking=True,
                    is_baggage_info_provided_by_pax=False,
                    is_no_changing_airport=False,
                    price_details=price_details,
                    baggages_info=baggages_info,
                    fares_info=fares_info,
                    routes=routes,
                    provider = Provider(
                        provider_id="",
                        name="Corendon Airlines",
                        index=None,
                        type="",
                        is_charter=True,
                        provider_index=None,
                        supplier_id="",
                        supplier_name="Corendon Airlines",
                    ),
                    supplier_provider = SupplierProvider(
                        provider_name="Corendon Airlines",
                        provider_office="",
                    ),
                )
                offers.append(offer)

    else:
        for out_route, out_fares in directions[0]:
            print(out_fares, '⬇️  Апсел ⬇️')
            print(out_route, '⬇️  Роут ⬇️')

            for ret_route, _ in directions[1]:
                routes = [out_route, ret_route]
                segment_keys = [seg.segment_key for seg in out_route.segments] + [seg.segment_key for seg in ret_route.segments]
                legs = [seg.leg for seg in out_route.segments] + [seg.leg for seg in ret_route.segments]
                has_upsell = len(out_fares) > 1

                for fare_data in out_fares:
                    price_info, price_details = convert_prices(fare_data, passenger_counts, currency)
                    fares_info = convert_fares_info(fare_data, segment_keys, legs, passenger_counts)
                    baggages_info = convert_baggages_info(fare_data, segment_keys, legs, passenger_counts)


                    offer = Offer(
                        offer_id=fare_data.get("FlightKey", str(uuid.uuid4())),
                        price_info=price_info,
                        reprice_available=True,
                        upsell=has_upsell,
                        booking=True,
                        is_baggage_info_provided_by_pax=False,
                        is_no_changing_airport=False,
                        price_details=price_details,
                        baggages_info=baggages_info,
                        fares_info=fares_info,
                        routes=routes,
                        provider = Provider(
                            provider_id="",
                            name="Corendon Airlines",
                            index=None,
                            type="",
                            is_charter=True,
                            provider_index=None,
                            supplier_id="",
                            supplier_name="Corendon Airlines",
                        ),
                        supplier_provider = SupplierProvider(
                            provider_name="Corendon Airlines",
                            provider_office="",
                        ),
                    )
                    offers.append(offer)

    return offers