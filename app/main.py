import base64
import httpx
import fastapi
import redis
from app.converters.search.request_converter import convert_search_request
from app.converters.search.response_converter import convert_search_response
from app.gts.schemas.common.direction import GtsSearchRequest
from app.integrations.corendon.schemas.common.auth import AuthCredentials
from app.integrations.corendon.schemas.common.booking import OptionConfirmBody, ModifySchemaBody,BookingCreateBody
from app.integrations.corendon.schemas.common.flight import FlightBookBody, FlightPriceBody

app = fastapi.FastAPI()

ram = redis.Redis(host='localhost', port=6379, decode_responses=True)


access_token  =''
surN =''
pnr =''
cont_type = 'application/x-www-form-urlencoded;charset=UTF-8'




@app.get("/")
def ddd():
    return {"token": "fffff"}


@app.post("/auth")
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
        t =ram.set("token", value=access_token)
        print(t, "Токен сохранился !!!!!!", ram.get("token"))


        return response.json()


@app.get("/flight")
async def flight_list():
    url = "https://apitest.corendonairlines.com/api/flight/list"

    tokenV = ram.get("token")

    headers = {
        "Authorization": f"Bearer {tokenV}",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        print(response.status_code,response.text, "get status")
        response.raise_for_status()

        print(response.json(), "responseee get")
        return response.json()



@app.post("/search")
async def flight_search(body: GtsSearchRequest):

    url = "https://apitest.corendonairlines.com/api/flight/search"
    tokenV = ram.get("token")

    headers = {
        "Authorization": f"Bearer {tokenV}",
        "Content-Type": "application/json",
    }

    corendon_body = convert_search_request(body)

    async with httpx.AsyncClient(timeout=30) as client:

        response = await client.post(
            url,
            headers=headers,
            json=corendon_body.model_dump()
        )

        print(response.status_code, "status")
        print(response.text, "response ⬇️")

        response.raise_for_status()

        corendon_data = response.json()
        gts_result = convert_search_response(corendon_data)
        print(gts_result, "gts_result ⬇️")

        return gts_result


@app.post("/price")
async def flight_price(body: FlightPriceBody):
    url = "https://apitest.corendonairlines.com/api/flight/price"
    tokenV = ram.get("token")
    headers = {
        "Authorization": f"Bearer {tokenV}",
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


@app.post("/basket/create")
async def basket_create(body: FlightBookBody):
    url = "https://apitest.corendonairlines.com/api/flight/basket/create"
    tokenV = ram.get("token")
    headers = {
        "Authorization": f"Bearer {tokenV}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
            json=body.model_dump()
        )
        print(response.status_code,response.text, "basket/create ответ и статус ➡️")
        response.raise_for_status()
        response.raise_for_status()
        return response.json()


@app.post("/booking")
async def flight_booking(body: BookingCreateBody):
    url = "https://apitest.corendonairlines.com/api/booking/create"
    global  pnr
    tokenV = ram.get("token")
    headers = {
        "Authorization": f"Bearer {tokenV}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
            json=body.model_dump()
        )
        print(response.text ,"Тело запроса ")
        print(response.status_code , "Статус")
        pnr_data = response.json()
        pnr = pnr_data["PNR"]
        ram.set("pnr", value=pnr)
        response.raise_for_status()
        return response.json()

@app.get("/ticket")
async def flight_ticket():
    global surN
    pnr = ram.get("pnr")
    url = f"https://apitest.corendonairlines.com/api/flight/booking/ticket/{pnr}"
    tokenV = ram.get("token")
    headers = {
        "Authorization": f"Bearer {tokenV}",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url , headers=headers)
        print(response.text,response.status_code, "Ответ  Текст  и Статус ⬇️")
        response.raise_for_status()
        data = response.json()
        passengers = data["Passengers"]
        surN = passengers[0]["LastName"]
        print(surN)
        p = ram.set("surname", value=surN)
        print(surN, f"Сохранился{p}")
        return response.json()

@app.get("/detail")
async def flight_detail():
    surname = ram.get("surname")
    tokenV = ram.get("token")
    pnr = ram.get("pnr")
    url = f"https://apitest.corendonairlines.com/api/flight/booking/detail/{pnr}/{surname}"
    headers = {
        "Authorization": f"Bearer {tokenV}",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url , headers=headers)
        response.raise_for_status()
        print(response.text, response.status_code,"Ответ прищел ⬇️")
        return  response.json()

@app.post("/option")
async def flight_option(body : OptionConfirmBody):
    tokenV = ram.get("token")
    url = "https://apitest.corendonairlines.com/api/booking/status/optionconfirmation"
    headers = {
        "Authorization": f"Bearer {tokenV}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            headers=headers,
            json=body.model_dump()
        )
        response.raise_for_status()
        print(response.text, response.status_code, "Пришел ответ ⬇️")
        return response.json()


@app.post("/modify")
async  def flight_modify (body : ModifySchemaBody):
    tokenV = ram.get("token")
    url = "https://apitest.corendonairlines.com/api/booking/modify"
    headers = {
        "Authorization": f"Bearer {tokenV}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            headers=headers,
            json=body.model_dump()
        )
        print(response.text, f" Статус : {response.status_code}", 'Ответ из /modify ⬇️')
        response.raise_for_status()
        return response.json()

