from typing import Any, Optional

from pydantic import BaseModel, Field

from app.gts.schemas.common.baggage import BaggageInfo
from app.gts.schemas.common.fare import FareInfo
from app.gts.schemas.common.price import PriceDetail, PriceInfo
from app.gts.schemas.common.provider import Provider, SupplierProvider
from app.gts.schemas.common.route import Route


class Other(BaseModel):
    FlightKey: list[str]



class Offer (BaseModel) :
    offer_id: str
    price_info: PriceInfo
    reprice_available: bool
    upsell: bool
    booking: bool
    is_baggage_info_provided_by_pax: bool
    is_no_changing_airport: bool
    price_details: list[PriceDetail]
    baggages_info: list[BaggageInfo]
    fares_info: list[FareInfo]
    routes: list[Route]
    provider: Provider
    supplier_provider: SupplierProvider
    other :  Optional[Other]  =  Field(default=None)


