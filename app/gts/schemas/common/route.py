from pydantic import BaseModel

from app.gts.schemas.common.segment import Segment
from app.gts.schemas.common.refund import RefundReissue


class Route (BaseModel) :
    route_index : int
    direction : str  #Это я пишу в ручную
    refundable : RefundReissue
    reissue : RefundReissue
    stops : int #- Незнаю что
    trip_time_minutes : int # Duration
    flight_time_minutes : int #TimeOnAir
    segments : list[Segment]

