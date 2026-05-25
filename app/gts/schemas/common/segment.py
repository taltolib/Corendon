from pydantic import BaseModel

from app.gts.schemas.common.airplane import AirplaneInfo

class Segment (BaseModel):
    segment_index: str
    segment_key : str
    leg : str #Нужно создать  в ручную
    flight_number : str #FlightNumber
    departure_country : str # DepartureCityName
    departure_country_code : str # DepartureCountryCode
    departure_city : str # DepartureCityName
    departure_city_code : str # DepartureCityCode
    departure_airport : str #DepartureAirportName
    departure_airport_code : str #DepartureAirportCode
    departure_date : str #DepartureDate
    departure_time : str # DepartureDate [time нужно только указать от этого]
    departure_timezone: str #
    arrival_country : str  #ArrivalCityName
    arrival_country_code :str # ArriveCountryCode
    arrival_city : str #ArrivalCityName
    arrival_city_code : str #ArrivalCityCode
    arrival_airport : str #ArrivalAirportName
    arrival_airport_code : str #ArrivalAirportCode
    arrival_terminal: str #
    arrival_date : str #ArriveDate
    arrival_time : str # ArriveDate[ time нужно только указать от этого]
    arrival_timezone : str  #
    duration_minutes : int   # Duration
    stop_time_minutes : int  #
    marketing_airline: str # AirCraftType
    marketing_airline_code : str # AirlineCode
    marketing_airline_logo: str #
    operating_airline : str # AirCraftType
    operating_airline_code: str # AirlineCode
    operating_airline_logo: str #
    seatmap_availability : bool #
    services_availability : bool #
    airplane_info : AirplaneInfo






