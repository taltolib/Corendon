from pydantic import BaseModel


class AirplaneInfo(BaseModel):
    airplane : str #AirCraftType
    airplane_code : str #AirlineCode
    seat_width : str #
    seat_angle : str #
    seat_scheme : str #
    seat_distance : str #
    has_wifi : bool #