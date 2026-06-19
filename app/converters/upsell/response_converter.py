import uuid
from app.converters.search.response_converter import (
    get_passenger_counts,
    convert_route,
    convert_prices,
    convert_fares_info,
    convert_baggages_info,
)
from app.gts.schemas.common.price import PriceInfo, PriceDetail
from app.gts.schemas.common.provider import Provider, SupplierProvider
from app.gts.schemas.common.upsell import Upsell, UpsellService
from app.gts.schemas.offer import Offer, Other


def build_services(fare_data: dict) -> list[UpsellService]:
    bag_kg = fare_data.get("Baggage", 0)
    hand_kg = fare_data.get("HandLuggage", 0)

    services = []

    if hand_kg > 0:
        services.append(UpsellService(
            name=f"Ручная кладь: 1 PC / {hand_kg} KG",
            status="included",
            is_bag=True,
        ))
    else:
        services.append(UpsellService(
            name="Ручная кладь: не включена",
            status="not included",
            is_bag=True,
        ))

    if bag_kg > 0:
        services.append(UpsellService(
            name=f"Багаж: {bag_kg} KG",
            status="included",
            is_bag=True,
        ))
    else:
        services.append(UpsellService(
            name="Багаж: не включен",
            status="not included",
            is_bag=True,
        ))

    services.append(UpsellService(
        name="Возврат не разрешен",
        status="not included",
        is_bag=False,
    ))
    services.append(UpsellService(
        name="Обмен не разрешен",
        status="not included",
        is_bag=False,
    ))
    print(f"➡️ Сервис:{services} ⬅️")
    return services


def convert_upsell_response(data: dict, offer_id: str) -> list[Offer]:
    offers = []
    passenger_counts = get_passenger_counts(data)
    currency = data.get("Currency", "EUR")
    flights_data = data.get("Flights", [])

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

    target_variant_index = None

    for i, (route, fares) in enumerate(directions[0]):
        flight_keys = [f.get("FlightKey", "") for f in fares]
        if offer_id in flight_keys:
            target_variant_index = i
            break

    if target_variant_index is None:
        print(f"Оffer_id не найден {offer_id}")
        return offers

    out_route, out_fares = directions[0][target_variant_index]
    has_upsell = len(out_fares) > 1

    if len(directions) == 1:

        segment_keys = []
        for seg in out_route.segments:
            segment_keys.append(seg.segment_key)

        legs = []
        for seg in out_route.segments:
            legs.append(seg.leg)

        for fare_data in out_fares:
            price_info, price_details = convert_prices(fare_data, passenger_counts, currency)
            fares_info = convert_fares_info(fare_data, segment_keys, legs, passenger_counts)
            baggages_info = convert_baggages_info(fare_data, segment_keys, legs, passenger_counts)

            fare_name = fare_data.get("AirFareName", "PUBLISHED")
            services = build_services(fare_data)
            for fi in fares_info:
                fi.upsell = Upsell(name=fare_name, services=services)

            offer = Offer(
                offer_id=str(uuid.uuid4()),
                price_info=price_info,
                reprice_available=True,
                upsell=has_upsell,
                booking=True,
                is_baggage_info_provided_by_pax=False,
                is_no_changing_airport=False,
                price_details=price_details,
                baggages_info=baggages_info,
                fares_info=fares_info,
                routes=[out_route],
                provider=Provider(
                    provider_id="",
                    name="Corendon Airlines",
                    index=None,
                    type="",
                    is_charter=True,
                    provider_index=None,
                    supplier_id="",
                    supplier_name="Corendon Airlines",
                ),
                supplier_provider=SupplierProvider(
                    provider_name="Corendon Airlines",
                    provider_office="",
                ),
                other=Other(
                    FlightKey=[fare_data.get("FlightKey", "")]
                )
            )
            offers.append(offer.model_dump())

    else:

        ret_route, ret_fares = directions[1][0]
        segment_keys = [seg.segment_key for seg in out_route.segments] + [seg.segment_key for seg in ret_route.segments]
        legs = [seg.leg for seg in out_route.segments] + [seg.leg for seg in ret_route.segments]

        for i, out_fare in enumerate(out_fares):
            ret_fare = ret_fares[i] if i < len(ret_fares) else ret_fares[0]

            out_price_info, out_price_details = convert_prices(out_fare, passenger_counts, currency)
            ret_price_info, ret_price_details = convert_prices(ret_fare, passenger_counts, currency)

            price_info = PriceInfo(
                price=out_price_info.price + ret_price_info.price,
                currency=currency,
                fee_amount=0.0,
                base_amount=out_price_info.base_amount + ret_price_info.base_amount,
                commission_amount=0.0,
                from_commission_amount=0.0,
                to_commission_amount=0.0,
            )

            price_details = []
            for j in range(len(out_price_details)):
                o = out_price_details[j]
                r = ret_price_details[j]
                price_details.append(
                    PriceDetail(
                        passenger_type=o.passenger_type,
                        currency=currency,
                        quantity=o.quantity,
                        single_base_amount=o.single_base_amount + r.single_base_amount,
                        single_tax_amount=o.single_tax_amount + r.single_tax_amount,
                        single_tax_details=0.0,
                        fee_amount=0.0,
                        to_commission_amount=0.0,
                        commission_amount=o.commission_amount,
                        single_total_amount=o.single_total_amount + r.single_total_amount,
                        base_total_amount=o.base_total_amount + r.base_total_amount,
                        tax_total_amount=o.tax_total_amount + r.tax_total_amount,
                        total_amount=o.total_amount + r.total_amount,
                        payable_amount=o.payable_amount + r.payable_amount,
                        single_fee_amount=0.0,
                        single_service_fee_amount=o.single_service_fee_amount,
                        single_commission_amount=o.single_commission_amount,
                        single_from_commission_amount=0.0,
                        single_to_commission_amount=0.0,
                        single_payable_amount=o.single_payable_amount + r.single_payable_amount,
                        service_fee_amount=o.service_fee_amount,
                        from_commission_amount=0.0,
                        profit_commission_amount=0.0,
                    ))

            fares_info = convert_fares_info(out_fare, segment_keys, legs, passenger_counts)
            baggages_info = convert_baggages_info(out_fare, segment_keys, legs, passenger_counts)

            fare_name = out_fare.get("AirFareName", "PUBLISHED")
            services = build_services(out_fare)
            for fi in fares_info:
                fi.upsell = Upsell(name=fare_name, services=services)

            print(fare_name, "⬆️  Апсел RT ⬆️")

            offer = Offer(
                offer_id=str(uuid.uuid4()),
                price_info=price_info,
                reprice_available=True,
                upsell=has_upsell,
                booking=True,
                is_baggage_info_provided_by_pax=False,
                is_no_changing_airport=False,
                price_details=price_details,
                baggages_info=baggages_info,
                fares_info=fares_info,
                routes=[out_route, ret_route],
                provider=Provider(
                    provider_id="",
                    name="Corendon Airlines",
                    index=None,
                    type="",
                    is_charter=True,
                    provider_index=None,
                    supplier_id="",
                    supplier_name="Corendon Airlines",
                ),
                supplier_provider=SupplierProvider(
                    provider_name="Corendon Airlines",
                    provider_office="",
                ),
                other=Other(
                    FlightKey=[out_fare.get("FlightKey", ""), ret_fare.get("FlightKey", "")]
                )
            )
            offers.append(offer.model_dump())

    return offers
