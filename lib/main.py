import base64
import httpx
import fastapi
from pydantic import BaseModel
from typing import List

app = fastapi.FastAPI()

access_token  =''
cont_type = 'application/x-www-form-urlencoded;charset=UTF-8'

class AuthCredentials(BaseModel):
    client_id: str = "CAI/fxQKTKpe63"
    client_secret: str = "uCQA2eddtbXLlrrQ"
    username: str
    password: str

class PassengerCounts(BaseModel):
    InfantCount: int
    AdultCount: int
    ChildCount: int


class FlightItem(BaseModel):
    DeparturePointCode: str
    FlightDate: str
    ArrivalPointCode: str
    DeparturePointType: str
    ArrivalPointType: str

class FlightSearchBody(BaseModel):
    TripType: str
    PassengerCounts: PassengerCounts
    CurrencyCode: str
    Flights: List[FlightItem]


class FlightPriceBody(BaseModel):
    TripType: str
    CurrencyCode: str
    PassengerCounts: PassengerCounts
    FlightKeys: list[str]

class Passenger(BaseModel):
    TravellerType: str
    Title: str
    FirstName: str
    LastName: str
    Birthdate: str
    NationalityCode: str = ""
    HealthCheckCode: str = ""

class FlightBookBody(BaseModel):
    Passengers: List[Passenger]
    TripType: str
    PassengerCounts: PassengerCounts  # уже есть у вас
    CurrencyCode: str
    FlightKeys: List[str]

@app.get("/")
def ddd():
    return {"token": "fffff"}


@app.post("/auth/token")
async def auth_user(credentials: AuthCredentials):
    global access_token
    url = "https://apitest.corendonairlines.com/oauth2/token"
    raw_key = f"{credentials.client_id}:{credentials.client_secret}"
    encoded_key = base64.b64encode(raw_key.encode()).decode()
    print(encoded_key)

    headers = {
    "Authorization": f"Basic {encoded_key}",
    "Content-Type": f'{cont_type}',
    }
    print(headers, "1")

    body = {
        "grant_type": "password",
        "username": credentials.username,
        "password": credentials.password,
    }
    print(body, "2")

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers,data=body  )
        print(response.text, response.status_code)
        response.raise_for_status()
        print(response.json() , "responseee")
        token_data = response.json()
        access_token = token_data["access_token"]
        return response.json()


@app.get("/api/flight/list")
async def flight_list():
    url = "https://apitest.corendonairlines.com/api/flight/list"
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        print(response.status_code,response.text, "get status")
        response.raise_for_status()

        # print(response.json(), "responseee get")
        return response.json()



@app.post("/api/flight/search")
async def flight_search(body: FlightSearchBody):

    url = "https://apitest.corendonairlines.com/api/flight/search"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:

        response = await client.post(
            url,
            headers=headers,
            json=body.model_dump()
        )

        print(response.status_code)
        print(response.text)

        response.raise_for_status()

        return response.json()


@app.post("/api/flight/price")
async def flight_price(body: FlightPriceBody):
    url = "https://apitest.corendonairlines.com/api/flight/price"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
            json=body.model_dump()
        )
        response.raise_for_status()
        return response.json()


@app.post("/api/flight/basket/create")
async def basket_create(body: FlightBookBody):
    url = "https://apitest.corendonairlines.com/api/flight/basket/create"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
            json=body.model_dump()
        )
        response.raise_for_status()
        return response.json()
