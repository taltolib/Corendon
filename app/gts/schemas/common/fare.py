from pydantic import BaseModel

from app.gts.schemas.common.upsell import Upsell
from app.integrations.corendon.schemas.common.passeger import PassengerType


class FareInfo (BaseModel):
    segment_keys : list[str] #- Незнаю
    leg : list[str] # Нужно создать  в ручную
    passenger_type : PassengerType #- Незнаю
    seats : int # RestPax # - Незнаю это ли  это
    upsell : Upsell
    fare_code : str #FareBasisCode
    service_class : str #AirFareName
    service_class_code : str #AirFareCode
    booking_class : str # PriceBandCode
    description : str | None #




