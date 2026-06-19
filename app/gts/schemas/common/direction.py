from pydantic import BaseModel, Field


class GtsDirection(BaseModel):
    departure: str
    arrival: str
    departure_date: str

class GtsSearchRequest(BaseModel):
    directions: list[GtsDirection]
    adt: int
    chd: int
    inf: int
    ins: int = 0
    currency: str = "USD"
    cabin_class: str = Field(default="",)
    flexible: bool = False
    direct: bool = False
    airlines: list[str] = []
    passengers_ids: list = []

class GtsUpsellRequest(BaseModel):
    offer_id : str


class GtsVerifyRequest(BaseModel):
    offer_id : str


class GtsPassenger(BaseModel):
    passenger_type: str       
    first_name: str
    last_name: str
    birth_date: str
    gender: str             
    nationality: str = Field(default="",)


class GtsContact(BaseModel):
    email: str
    phone: str = ""


class GtsBookingRequest(BaseModel):
    offer_id: str
    flight_keys: list[str]    
    trip_type: str = "1"      
    currency: str = "USD"
    adt: int = 1
    chd: int = 0
    inf: int = 0
    passengers: list[GtsPassenger]
    contact: GtsContact