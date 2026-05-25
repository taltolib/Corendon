from pydantic import BaseModel

from app.gts.schemas.data import ResponseData


class FlightSearchRespose (BaseModel):
    status : str #-
    call_id : str #-
    call_time : str #-
    message : str #-
    code : int #-
    data : ResponseData #-
    error : str #-
