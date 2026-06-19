from app.converters.search.response_converter import (
    get_passenger_counts,
    convert_route,
    convert_prices,
    convert_fares_info,
    convert_baggages_info,
    check_is_no_changing_airport,
)
from app.gts.schemas.common.price import PriceInfo, PriceDetail
from app.gts.schemas.common.provider import Provider, SupplierProvider
from app.gts.schemas.offer import Offer, Other


def convert_verify_response ( price_data : dict, offer_id : str ) -> dict :

    available   = price_data.get("AvailableForOption", True)
    option_date = price_data.get("OptionDate", "")

    if not available :
        return {
            "status": "error",
            "verified": False,
            "offer_id" : offer_id,
            "option_date": option_date,
            "message" : "Предложение больше недоступно",
        }

    passenger_counts = get_passenger_counts(price_data)
    currency= price_data.get("Currency", "USD")
    flights_data = price_data.get("Flights", [])

    if not flights_data :
        return {"status": "error", "verified": False, "offer_id": offer_id, "message": "Нет рейсов в ответ на запрос цены ( "}

    if len(flights_data) == 1 :

        route_variant = flights_data[0].get("Value", [])[0]
        route_data= route_variant.get("Key", {})
        fare_variants = route_variant.get("Value", [])

        if not fare_variants :
            return {"status": "error", "verified": False, "offer_id": offer_id, "message": "no fares in price response"}

        fare_data = fare_variants[0]

        if fare_data.get("RestPax", 1) == 0 :
            return {"status": "error", "verified": False, "offer_id": offer_id, "option_date": option_date, "message": "no seats available"}

        route  = convert_route(route_data, 1)
        routes = [route]

        segment_keys = []
        for seg in route.segments :
            segment_keys.append(seg.segment_key)

        legs = []
        for seg in route.segments :
            legs.append(seg.leg)

        price_info, price_details = convert_prices(fare_data, passenger_counts, currency)
        fares_info    = convert_fares_info(fare_data, segment_keys, legs, passenger_counts)
        baggages_info = convert_baggages_info(fare_data, segment_keys, legs, passenger_counts)

        offer = Offer(
            offer_id= offer_id,
            price_info= price_info,
            reprice_available= False,
            upsell= False,
            booking = True,
            is_baggage_info_provided_by_pax = False,
            is_no_changing_airport = check_is_no_changing_airport(routes),
            price_details= price_details,
            baggages_info= baggages_info,
            fares_info= fares_info,
            routes= routes,
            provider = Provider(
                provider_id = "",
                name= "Corendon Airlines",
                index= None,
                type= "",
                is_charter= True,
                provider_index= None,
                supplier_id = "",
                supplier_name = "Corendon Airlines",
            ),
            supplier_provider = SupplierProvider(
                provider_name = "Corendon Airlines",
                provider_office = "",
            ),
            other=Other(
                FlightKey =[fare_data.get("FlightKey", offer_id)]
            ),
        )

    else :
        out_variant= flights_data[0].get("Value", [])[0]
        ret_variant= flights_data[1].get("Value", [])[0]

        out_route_data= out_variant.get("Key", {})
        ret_route_data= ret_variant.get("Key", {})
        out_fare_variants = out_variant.get("Value", [])
        ret_fare_variants = ret_variant.get("Value", [])

        if not out_fare_variants :
            return {"status": "error", "verified": False, "offer_id": offer_id, "message": "Отсутствие тарифов в ценовом ответе"}

        out_fare = out_fare_variants[0]
        ret_fare = ret_fare_variants[0] if ret_fare_variants else {}

        if out_fare.get("RestPax", 1) == 0 :
            return {"status": "error", "verified": False, "offer_id": offer_id, "option_date": option_date, "message": "Мест нет"}

        out_route = convert_route(out_route_data, 1)
        ret_route = convert_route(ret_route_data, 2)
        routes    = [out_route, ret_route]

        segment_keys = []
        for seg in out_route.segments :
            segment_keys.append(seg.segment_key)
        for seg in ret_route.segments :
            segment_keys.append(seg.segment_key)

        legs = []
        for seg in out_route.segments :
            legs.append(seg.leg)
        for seg in ret_route.segments :
            legs.append(seg.leg)


        out_price_info, out_price_details = convert_prices(out_fare, passenger_counts, currency)
        ret_price_info, ret_price_details = convert_prices(ret_fare, passenger_counts, currency)


        price_info = PriceInfo(
            price = out_price_info.price+ ret_price_info.price,
            currency= currency,
            fee_amount= 0.0,
            base_amount = out_price_info.base_amount + ret_price_info.base_amount,
            commission_amount= 0.0,
            from_commission_amount= 0.0,
            to_commission_amount= 0.0,
        )

        price_details = []
        for out_d, ret_d in zip(out_price_details, ret_price_details) :
            price_details.append(
                PriceDetail(
                passenger_type= out_d.passenger_type,
                currency = currency,
                quantity = out_d.quantity,
                single_base_amount = out_d.single_base_amount +ret_d.single_base_amount,
                single_tax_amount= out_d.single_tax_amount     + ret_d.single_tax_amount,
                single_tax_details= 0.0,
                fee_amount= 0.0,
                to_commission_amount= 0.0,
                commission_amount= out_d.commission_amount,
                single_total_amount= out_d.single_total_amount + ret_d.single_total_amount,
                base_total_amount= out_d.base_total_amount  + ret_d.base_total_amount,
                tax_total_amount= out_d.tax_total_amount + ret_d.tax_total_amount,
                total_amount= out_d.total_amount + ret_d.total_amount,
                payable_amount= out_d.payable_amount + ret_d.payable_amount,
                single_fee_amount= 0.0,
                single_service_fee_amount= out_d.single_service_fee_amount,
                single_commission_amount= out_d.single_commission_amount,
                single_from_commission_amount= 0.0,
                single_to_commission_amount = 0.0,
                single_payable_amount= out_d.single_payable_amount + ret_d.single_payable_amount,
                service_fee_amount = out_d.service_fee_amount,
                from_commission_amount = 0.0,
                profit_commission_amount = 0.0,
            )
            )

        fares_info= convert_fares_info(out_fare, segment_keys, legs, passenger_counts)
        baggages_info = convert_baggages_info(out_fare, segment_keys, legs, passenger_counts)

        out_key = out_fare.get("FlightKey", offer_id)
        ret_key = ret_fare.get("FlightKey", "")

        offer = Offer(
            offer_id= offer_id,
            price_info= price_info,
            reprice_available= False,
            upsell= False,
            booking= True,
            is_baggage_info_provided_by_pax = False,
            is_no_changing_airport= check_is_no_changing_airport(routes),
            price_details= price_details,
            baggages_info = baggages_info,
            fares_info= fares_info,
            routes= routes,
            provider = Provider(
                provider_id= "",
                name = "Corendon Airlines",
                index = None,
                type = "",
                is_charter = True,
                provider_index= None,
                supplier_id = "",
                supplier_name= "Corendon Airlines",
            ),
            supplier_provider= SupplierProvider(
                provider_name= "Corendon Airlines",
                provider_office= "",
            ),
            other = Other(
                FlightKey = [out_key, ret_key]
            ),
        )

    return {
        "status": "success",
        "verified": True,
        "offer_id": offer_id,
        "option_date": option_date,
        "offer": offer.model_dump(),
    }
