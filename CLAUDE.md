# Corendon Airlines API Integration — Project Context

## Что это за проект

FastAPI-приложение: интеграционный слой между Corendon Airlines API и внутренним GTS-форматом.
Тестовый домен: `https://apitest.corendonairlines.com`
Продакшн домен: `https://api.corendonairlines.com`

---

## Структура проекта

```
app/
├── main.py                          — FastAPI приложение, все эндпоинты
├── router.py                        — заглушка, не используется
├── converters/
│   ├── request_converter.py         — конвертация запросов (пока пустой)
│   └── response_converter.py        — конвертация ответов Corendon → GTS
├── gts/
│   └── schemas/
│       ├── data.py                  — ResponseData
│       ├── offer.py                 — Offer
│       ├── status.py                — FlightSearchResponse
│       └── common/
│           ├── enums.py             — TripType, PassengerType
│           ├── route.py             — Route
│           ├── segment.py           — Segment
│           ├── airplane.py          — AirplaneInfo
│           ├── price.py             — PriceInfo, PriceDetail
│           ├── refund.py            — RefundReissue
│           ├── upsell.py            — Upsell
│           ├── baggage.py           — BaggageInfo, BaggageAllowance, HandBaggage
│           ├── fare.py              — FareInfo
│           └── provider.py          — Provider, SupplierProvider
└── integrations/
    └── corendon/
        └── schemas/
            ├── request.py
            └── common/
                ├── auth.py          — AuthCredentials
                ├── flight.py        — FlightSearchBody, FlightPriceBody, FlightBookBody
                ├── passeger.py      — Passenger, PassengerType  (опечатка в имени файла — оставить как есть)
                ├── payment.py       — PaymentSchema, CreditCardSchema, ContactInformationSchema
                └── booking.py       — BookingCreateBody, OptionConfirmBody, ModifySchemaBody
```

---

## Стек

- **FastAPI** — веб-фреймворк
- **Pydantic** — схемы и валидация
- **httpx** — async HTTP-клиент для вызовов Corendon API
- **redis** — хранение токена, PNR, фамилии между запросами (`localhost:6379`)

---

## Аутентификация Corendon API

OAuth 2.0, grant_type=password.

```
POST /oauth2/token
Authorization: Basic base64(client_id:client_secret)
Content-Type: application/x-www-form-urlencoded
Body: grant_type=password&username=...&password=...
```

Токен кладётся в Redis: `ram.set("token", value=access_token)`
Потом везде достаётся: `tokenV = ram.get("token")`

---

## Реализованные эндпоинты в main.py

| Эндпоинт | Метод | Corendon URL | Описание |
|---|---|---|---|
| `/auth` | POST | `/oauth2/token` | Получить Bearer-токен |
| `/flight` | GET | `/api/flight/list` | Список всех рейсов |
| `/search` | POST | `/api/flight/search` | Поиск рейсов |
| `/price` | POST | `/api/flight/price` | Получить цены |
| `/basket/create` | POST | `/api/flight/basket/create` | Создать корзину (pre-booking) |
| `/booking` | POST | `/api/booking/create` | Создать бронирование |
| `/ticket` | GET | `/api/flight/booking/ticket/{pnr}` | Список билетов по PNR |
| `/detail` | GET | `/api/flight/booking/detail/{pnr}/{surname}` | Детали бронирования |
| `/option` | POST | `/api/booking/status/optionconfirmation` | Подтвердить опционное бронирование |
| `/modify` | POST | `/api/booking/modify` | Отменить бронирование |

---

## Паттерн эндпоинта (как писать новые)

```python
@app.post("/endpoint")
async def endpoint_name(body: SomeSchema):
    url = "https://apitest.corendonairlines.com/api/..."
    tokenV = ram.get("token")
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
        print(response.text, response.status_code, "описание ⬇️")
        response.raise_for_status()
        return response.json()
```

Для GET-запросов — без `json=body.model_dump()`, без `Content-Type`.

---

## Соглашения по коду (стиль автора)

- Схемы Corendon: поля с **PascalCase** (как в документации API)
- Схемы GTS: поля со **snake_case**
- Pydantic `BaseModel` — наследуются все схемы
- `Optional` и `| None` используются оба варианта
- Дефолтные значения ставятся прямо в поле: `field: str = ""`
- `List[...]` и `list[...]` — оба встречаются
- Глобальные переменные: `access_token`, `surN`, `pnr` (сохраняются и в Redis)
- `print()` — используется для отладки, оставлять как есть
- Русские комментарии и print-строки — норма
- Комментарии в схемах показывают маппинг полей Corendon → GTS

---

## Два формата схем

### Corendon-схемы (`app/integrations/corendon/schemas/`)
Отражают структуру JSON из документации Corendon. PascalCase поля.

```python
class FlightItem(BaseModel):
    DeparturePointCode: str
    FlightDate: str
    ArrivalPointCode: str
    DeparturePointType: str
    ArrivalPointType: str
```

### GTS-схемы (`app/gts/schemas/`)
Внутренний унифицированный формат. snake_case поля.

```python
class Segment(BaseModel):
    segment_index: str
    segment_key: str
    leg: str
    flight_number: str
    ...
```

---

## Конвертеры (`app/converters/response_converter.py`)

Вспомогательные функции для преобразования Corendon-ответа в GTS:

| Функция | Что делает |
|---|---|
| `ms_to_minutes(ms)` | Миллисекунды → минуты |
| `split_time(dt_str)` | ISO-строка → (date, time) |
| `passanger_type_gts(int)` | 1/2/3 → adult/child/infant |
| `trip_type_gts(str)` | "1"/"2"/"3" → one_way/round_trip/multi_city |
| `convert_segment(dict, int)` | Corendon сегмент → GTS Segment |
| `convert_route(dict, dict, int)` | Corendon маршрут → GTS Route |
| `convert_prices(dict)` | Corendon fare → (PriceInfo, list[PriceDetail]) |

`segment_key` генерируется через `hashlib.sha256(secrets.token_hex(8).encode()).hexdigest()`

---

## Enum-значения GTS

```python
class TripType(str, Enum):
    one_way = "OW"
    round_trip = "RT"
    multi_city = "MC"

class PassengerType(str, Enum):
    adult = "ADT"
    child = "CHD"
    infant = "INF"
    infant_with_seat = "INS"
```

---

## TravellerType в Corendon API

| Значение | Тип |
|---|---|
| 1 | Adult |
| 2 | Child |
| 3 | Infant |

## TripType в Corendon API

| Значение | Тип |
|---|---|
| 1 | OneWay |
| 2 | RoundTrip |

## PointType в Corendon API

| Значение | Тип |
|---|---|
| 0 | Airport |
| 1 | City |

---

## Redis-ключи

| Ключ | Что хранит |
|---|---|
| `token` | Bearer access token |
| `pnr` | Последний PNR бронирования |
| `surname` | Фамилия первого пассажира |

---

## Важные детали

- Файл называется `passeger.py` (опечатка) — не переименовывать
- `PriceDetail` в `price.py` — не наследует `BaseModel` (так и есть у автора)
- В `booking.py` у `/basket/create` есть дублирующий `response.raise_for_status()` — не трогать
- Credentials по умолчанию захардкожены в `AuthCredentials`: `client_id = "CAI/fxQKTKpe63"`, `client_secret = "uCQA2eddtbXLlrrQ"`
- Незаполненные/неизвестные поля GTS — пустая строка `""` или `False` или `None`
- `departure_timezone` и `arrival_timezone` — всегда `""`
- `seatmap_availability` и `services_availability` — всегда `False`

---

## Workflow бронирования (порядок вызовов)

1. `/auth` → получить токен
2. `/search` → найти рейсы, получить FlightKey
3. `/price` → уточнить цены по FlightKey
4. `/basket/create` → создать корзину, получить BasketKey
5. `/booking` → создать бронирование, получить PNR
6. `/ticket` → получить номер билета и фамилию
7. `/detail` → получить детали бронирования
8. `/option` (опционально) → подтвердить опционное бронирование
9. `/modify` → отменить бронирование

---

## Следующие интеграции (ещё не реализованы)

По документации остались:
- **Cancel Ticket** — `POST /api/flight/booking/cancel/ticket` (нужна схема `CancelTicketBody` с `Pnr` и `TicketNumbers`)
- **Ticket Report** — `POST /api/flight/booking/ticket/report` (нужна схема `TicketReportBody`)
- **Get Ticket Detail For Cancellation** — `POST /api/flight/booking/cancel/detail` (нужна схема с `Pnr`)
- **request_converter.py** — конвертация GTS-запроса в Corendon-формат (пока пустой)
- **convert_prices** — функция не завершена (нет `return` и формирования `PriceInfo`)
