from pydantic import BaseModel
from typing import List, Optional
from pydantic import BaseModel
from typing import Optional


class CreditCardSchema(BaseModel):
    CardType: int
    CardNumber: str
    ExpireMonth: int
    ExpireYear: int
    Cvc: str
    FullName: str


class PhoneInformationSchema(BaseModel):
    CountryCode: str
    AreaCode: str
    Number: str


class PaymentSchema(BaseModel):
    CreditCard: CreditCardSchema | None = None
    CurrencyCode: str
    PaymentMethodCode: str


class ContactInformationSchema(BaseModel):
    Title: str
    FirstName: str
    LastName: str
    Phone: str
    PhoneInformation: PhoneInformationSchema | None = None
    Email: str
    BirthDate: str
    CountryCode: str | None = None


class BookingCreateBody(BaseModel):
    BasketKey: str
    OptionReservation: bool | None = False
    SalesSourceCode: str | None = ""
    BookingLanguageCode: str | None = "EN"
    SalesAmount: str
    Payment: PaymentSchema
    ContactInformation: ContactInformationSchema