from pydantic import BaseModel

from app.gts.schemas.common.enums import TripType
from app.gts.schemas.offer import Offer


class ResponseData (BaseModel) :
    request_id : str #- Незнаю # нужно генерировать
    trip_type : TripType #-
    sort_type : str #-
    currency : str #-
    count : int #-
    next_token : str #-
    offers : list[Offer]



