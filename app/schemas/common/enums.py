from enum import Enum


class TripType(str, Enum):
    one_way = "OW"
    round_trip = "RT"
    multi_city = "MC"


class PassengerType(str, Enum):
    adult = "ADT"
    child = "CHD"
    infant = "INF"
    infant_with_seat = "INS"

