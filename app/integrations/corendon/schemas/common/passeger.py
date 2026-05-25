from pydantic import BaseModel


class PassengerType(BaseModel):
    InfantCount: int
    AdultCount: int
    ChildCount: int

class Passenger(BaseModel):
    TravellerType: str
    Title: str
    FirstName: str
    LastName: str
    Birthdate: str
    NationalityCode: str = ""
    HealthCheckCode: str = ""

