import base64
import json
import httpx
import fastapi
import redis
import os
from app.converters.search.request_converter import convert_search_request
from app.converters.search.response_converter import convert_search_response
from app.converters.upsell.response_converter import convert_upsell_response
from app.converters.verify.request_converter import build_verify_request
from app.converters.verify.response_converter import convert_verify_response
from app.gts.schemas.common.direction import GtsSearchRequest, GtsUpsellRequest, GtsBookingRequest, GtsVerifyRequest
from app.integrations.corendon.schemas.common.auth import AuthCredentials
from app.integrations.corendon.schemas.common.booking import OptionConfirmBody, ModifySchemaBody, BookingCreateBody
from app.integrations.corendon.schemas.common.flight import FlightBookBody

app = fastapi.FastAPI()

ram = redis.Redis(host='localhost', port=6379, decode_responses=True)

access_token = ''
surN = ''
pnr = ''
cont_type = 'application/x-www-form-urlencoded;charset=UTF-8'


def save_res(name, content):
    print("Текущая директория:", os.getcwd())
    print("Сохраняю:", name)
    try:
        with open(name, "w", encoding="utf-8") as file:
            json.dump(content, file, ensure_ascii=False, indent=4)
        print("Файл сохранён")
    except Exception as e:
        print("Ошибка:", e)


@app.get("/")
def root():
    return {"user": "Все хорошо  :) "}


@app.get("/flush")
def flush_redis():
    ram.flushdb()
    return {"status": "Redis очищен"}


@app.post("/auth")
async def auth_user(credentials: AuthCredentials):
    global access_token
    url = "https://apitest.corendonairlines.com/oauth2/token"
    raw_key = f"{credentials.client_id}:{credentials.client_secret}"
    encoded_key = base64.b64encode(raw_key.encode()).decode()
    print(encoded_key)

    headers = {
        "Authorization": f"Basic {encoded_key}",
        "Content-Type": f"{cont_type}",
    }
    body = {
        "grant_type": "password",
        "username": credentials.username,
        "password": credentials.password,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, data=body)
        print(response.text, response.status_code)
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data["access_token"]
        t = ram.set("token", value=access_token)
    
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
        print(response.status_code, response.text, "get status")
        response.raise_for_status()
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
        
        ram.set("data", value=json.dumps(corendon_data))
        
        gts_result = convert_search_response(corendon_data)
        
        save_res("app/file/cor_respose.json", corendon_data)
        save_res("app/file/gts_respose.json", gts_result)

        for offer in gts_result:
            o_id = offer["offer_id"]
            all_keys = offer.get("other", {}).get("FlightKey", [])
            routes = offer.get("routes", [])
            
            if len(routes) > 1 :
                trip_type = "2"
            else :
                trip_type = "1"
                
            ram.set(f"offer:{o_id}", json.dumps({
                "offer_id": o_id,
                "flight_keys": all_keys,
                "trip_type": trip_type,
                "adt": body.adt,
                "chd": body.chd,
                "inf": body.inf,
                "currency": body.currency,
            }))
            
            for key in all_keys:
                if key:
                    base_key = key.split("#")[0]
                    ram.set(f"fkey:{base_key}", o_id)

        return gts_result


@app.post("/upsell")
async def offer_upsell(body: GtsUpsellRequest):
    data = ram.get("data")
    meta_raw = ram.get(f"offer:{body.offer_id}")
    if not meta_raw:
        return {"status": "error", "message": "сначала делаейте сеац"}

    meta = json.loads(meta_raw)
    print(f"✅🪄  Offer_id  ответ от redis {meta}")
    flight_key = meta["flight_keys"][0]
    print(f"✈️🗝️  FlightKey  ответ от redis {flight_key}")

    upsell_result = convert_upsell_response(json.loads(data), flight_key)
    
    for offer in upsell_result:
        all_keys = offer.get("other", {}).get("FlightKey", [])
        if all_keys :
            fk = all_keys[0]
        else :
            fk = None

        routes = offer.get("routes", [])
        if len(routes) > 1 :
            trip_type = "2"
        else :
            trip_type = "1"

        if fk :
            base_fk = fk.split("#")[0]
        else :
            base_fk = None

        if base_fk :
            existing_id = ram.get(f"fkey:{base_fk}")
        else :
            existing_id = None
            
        print(f"🔍 fk={fk}")
        print(f"🔍 base_fk={base_fk}")
        print(f"🔍 existing_id={existing_id}")
        if existing_id:
            offer["offer_id"] = existing_id
        else:
            o_id = offer["offer_id"]
            ram.set(f"offer:{o_id}", json.dumps({
                "offer_id": o_id,
                "flight_keys": all_keys,
                "trip_type": trip_type,
                "adt": meta["adt"],
                "chd": meta["chd"],
                "inf": meta["inf"],
                "currency": meta["currency"],
            }))
            if base_fk:
                ram.set(f"fkey:{base_fk}", o_id)

    return upsell_result


@app.post("/verify")
async def flight_verify(body: GtsVerifyRequest):
    url = "https://apitest.corendonairlines.com/api/flight/price"
    tokenV = ram.get("token")
    headers = {
        "Authorization": f"Bearer {tokenV}",
        "Content-Type": "application/json",
    }

    meta_raw = ram.get(f"offer:{body.offer_id}")
    if not meta_raw:
        return {"status": "error", "message": "offer not found, сначала сделай /search"}

    meta = json.loads(meta_raw)
    price_body = build_verify_request(meta)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
            json=price_body.model_dump()
        )
        print(response.status_code, response.text, "verify ответ ➡️")
        response.raise_for_status()

        price_data = response.json()
        return convert_verify_response(price_data, body.offer_id)


@app.post("/basket")
async def basket_from_gts(body: GtsBookingRequest):
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
        print(response.status_code, response.text, "basket ответ и статус ➡️")
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
        print(response.status_code, response.text, "basket/create ответ и статус ➡️")
        response.raise_for_status()
        return response.json()


@app.post("/booking")
async def flight_booking(body: BookingCreateBody):
    global pnr
    url = "https://apitest.corendonairlines.com/api/booking/create"
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
        print(response.text, "Тело запроса ")
        print(response.status_code, "Статус")
        pnr_data = response.json()
        pnr = pnr_data["Pnr"]
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
        response = await client.get(url, headers=headers)
        print(response.text, response.status_code, "Ответ Текст и Статус ⬇️")
        response.raise_for_status()
        data = response.json()
        passengers = data["Passengers"]
        surN = passengers[0]["LastName"]
        p = ram.set("surname", value=surN)
        print(surN, f"Сохранился {p}")
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
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        print(response.text, response.status_code, "Ответ пришел ⬇️")
        return response.json()


@app.post("/option")
async def flight_option(body: OptionConfirmBody):
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
async def flight_modify(body: ModifySchemaBody):
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
        print(response.text, f"Статус: {response.status_code}", "Ответ из /modify ⬇️")
        response.raise_for_status()
        return response.json()
