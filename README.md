# Corendon Airlines API Integration

Интеграционный слой между системой **GTS (Global Travel System)** и API авиакомпании **Corendon Airlines**.
Сервис принимает запросы в формате GTS, конвертирует их в формат Corendon, отправляет запросы к Corendon API и возвращает ответы обратно в формате GTS.

---

## Технологии

| Инструмент | Назначение |
|---|---|
| **FastAPI** | Web-фреймворк, REST API |
| **Pydantic** | Валидация данных, схемы |
| **httpx** | Async HTTP-клиент для запросов к Corendon |
| **Redis** | Хранение токенов, PNR, данных пассажиров между запросами |
| **Python 3.10+** | Язык разработки |

---

## Структура проекта

```
Corendon/
├── app/
│   ├── main.py                          # FastAPI приложение, все эндпоинты
│   ├── router.py                        # APIRouter (заготовка)
│   ├── file/
│   │   ├── cor_respose.json             # Пример ответа от Corendon API
│   │   └── gts_respose.json             # Пример ответа в формате GTS
│   ├── converters/
│   │   ├── search/
│   │   │   ├── request_converter.py     # GTS запрос → Corendon запрос
│   │   │   └── response_converter.py    # Corendon ответ → GTS ответ
│   │   └── upsell/
│   │       ├── request_converter.py     # (в разработке)
│   │       └── response_converter.py    # (в разработке)
│   ├── gts/
│   │   └── schemas/
│   │       ├── offer.py                 # Модель Offer
│   │       ├── data.py                  # ResponseData
│   │       ├── status.py                # FlightSearchResponse
│   │       └── common/
│   │           ├── direction.py         # GtsDirection, GtsSearchRequest
│   │           ├── segment.py           # Сегмент рейса
│   │           ├── route.py             # Маршрут
│   │           ├── price.py             # Цены
│   │           ├── fare.py              # Тарифы
│   │           ├── baggage.py           # Багаж
│   │           ├── provider.py          # Провайдер / авиакомпания
│   │           ├── refund.py            # Возврат / обмен
│   │           ├── airplane.py          # Информация о самолёте
│   │           ├── upsell.py            # Допуслуги
│   │           └── enums.py             # TripType, PassengerType
│   └── integrations/
│       └── corendon/
│           └── schemas/
│               ├── request.py           # Обёртки запросов
│               └── common/
│                   ├── auth.py          # AuthCredentials
│                   ├── flight.py        # FlightSearchBody, FlightPriceBody
│                   ├── booking.py       # BookingCreateBody, OptionConfirmBody
│                   ├── passeger.py      # Passenger
│                   └── payment.py       # PaymentSchema, CreditCardSchema
└── README.md
```

---

## API Эндпоинты

### Аутентификация

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/auth` | Получить OAuth2 токен от Corendon API |

**Body:**
```json
{
  "client_id": "CAI/*********",
  "client_secret": "u*********Q",
  "username": "your_username",
  "password": "your_password"
}
```
Токен сохраняется в Redis и используется во всех последующих запросах.

---

### Поиск рейсов

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/flight` | Список доступных рейсов |
| `POST` | `/search` | Поиск рейсов по параметрам |

**POST /search — Body (формат GTS):**
```json
{
  "directions": [
    {
      "departure": "TAS",
      "arrival": "IST",
      "departure_date": "2026-07-15"
    }
  ],
  "adt": 2,
  "chd": 0,
  "inf": 0,
  "currency": "USD",
  "cabin_class": "Economy",
  "direct": false,
  "flexible": false,
  "airlines": [],
  "passengers_ids": []
}
```

**Логика конвертации:**
- 1 направление → `TripType = "1"` (one-way)
- 2 направления → `TripType = "2"` (round-trip)
- 3+ направлений → `TripType = "3"` (multi-city)

---

### Бронирование

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/price` | Получить актуальную цену по flight keys |
| `POST` | `/basket/create` | Создать корзину (basket) |
| `POST` | `/booking` | Создать бронирование, получить PNR |
| `GET` | `/ticket` | Получить данные билета по PNR |
| `GET` | `/detail` | Детали бронирования |
| `POST` | `/option` | Подтверждение опции |
| `POST` | `/modify` | Изменение бронирования |

**Полный флоу бронирования:**
```
/search → /price → /basket/create → /booking → /ticket → /detail
```

---

### Допуслуги

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/upsell` | Получить допуслуги (в разработке) |

---

## Конвертеры

### `converters/search/request_converter.py`
Конвертирует `GtsSearchRequest` → `FlightSearchBody` для Corendon API.

### `converters/search/response_converter.py`
Конвертирует ответ Corendon → список `Offer` в формате GTS.

Ключевые функции:

| Функция | Что делает |
|---|---|
| `convert_segment()` | Преобразует данные сегмента рейса |
| `convert_route()` | Группирует сегменты в маршруты |
| `convert_prices()` | Разбивает цены по типам пассажиров |
| `convert_fares_info()` | Извлекает тарифную информацию |
| `convert_baggages_info()` | Извлекает нормы багажа |
| `convert_search_response()` | Главная функция — собирает итоговый список Offer |

Для **round-trip** формирует офферы по комбинациям: каждый тариф туда + каждый маршрут обратно.

---

## Схемы данных

### GTS — Входящий запрос поиска

```
GtsSearchRequest
├── directions: list[GtsDirection]
│   ├── departure: str        # IATA код аэропорта вылета
│   ├── arrival: str          # IATA код аэропорта прилёта
│   └── departure_date: str   # Дата вылета
├── adt: int                  # Количество взрослых
├── chd: int                  # Количество детей
├── inf: int                  # Количество младенцев
├── currency: str             # Валюта (USD по умолчанию)
├── cabin_class: str          # Класс (Economy / Business)
└── direct: bool              # Только прямые рейсы
```

### GTS — Оффер (ответ)

```
Offer
├── offer_id: str
├── price_info: PriceInfo         # Общая стоимость
├── price_details: list[PriceDetail]  # Разбивка по пассажирам
├── routes: list[Route]           # Маршруты (сегменты рейса)
├── baggages_info: list[BaggageInfo]  # Нормы багажа
├── fares_info: list[FareInfo]    # Тарифы
├── provider: Provider            # Авиакомпания
└── upsell: bool                  # Доступны допуслуги
```

---

## Хранение состояния (Redis)

| Ключ | Значение | Когда сохраняется |
|---|---|---|
| `access_token` | OAuth2 Bearer токен | `/auth` |
| `pnr` | Номер бронирования | `/booking` |
| `surN` | Фамилия пассажира | `/ticket` |

---

## Запуск

### Зависимости

```bash
pip install fastapi uvicorn httpx pydantic redis
```

### Запуск Redis

```bash
# Windows (через Docker)
docker run -d -p 6379:6379 redis

# Или WSL / Linux
redis-server
```

### Запуск приложения

```bash
uvicorn app.main:app --reload
```

Приложение будет доступно по адресу: `http://localhost:8000`

Документация Swagger UI: `http://localhost:8000/docs`

---

## Пример использования

### 1. Авторизация
```bash
curl -X POST http://localhost:8000/auth \
  -H "Content-Type: application/json" \
  -d '{"client_id":"CAI/fxQKTKpe63","client_secret":"uCQA2eddtbXLlrrQ","username":"user","password":"pass"}'
```

### 2. Поиск рейсов
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "directions": [{"departure":"TAS","arrival":"IST","departure_date":"2026-07-15"}],
    "adt": 1, "chd": 0, "inf": 0,
    "currency": "USD", "cabin_class": "Economy",
    "direct": false, "flexible": false,
    "airlines": [], "passengers_ids": []
  }'
```

---

## Автор

**Tolib Talibov** — [GitHub](https://github.com/taltolib) · [Telegram](https://t.me/taltolib)
