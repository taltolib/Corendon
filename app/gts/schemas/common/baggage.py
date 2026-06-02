from typing import Optional

from pydantic import BaseModel

from app.gts.schemas.common.enums import PassengerType


class BaggageSize (BaseModel):
    height : Optional[float] #
    width : Optional[float]  #Только есть этот метка
    length : Optional[float] #
    unit : str  #


class BaggageAllowance (BaseModel):
    value : float
    unit : str #ЭТо килограм или cp
    size : BaggageSize

class HandBaggage (BaseModel):
    value : float #
    unit : str ##ЭТо килограм или cp  # этого тоже нет
    weight : float  # Только это метод есть
    size : BaggageSize #

class BaggageInfo (BaseModel):
    segment_keys : list[str] #- Незнаю
    leg : list[str] # Нужно создать самому
    passenger_type : PassengerType
    baggage : BaggageAllowance
    hand_baggage : HandBaggage
    description : str # #- незнаю для чего