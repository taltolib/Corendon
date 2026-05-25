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
    CreditCard: Optional[CreditCardSchema] = None
    CurrencyCode: str
    PaymentMethodCode: str

class ContactInformationSchema(BaseModel):
    Title: str
    FirstName: str
    LastName: str
    Phone: str
    PhoneInformation: Optional[PhoneInformationSchema] = None
    Email: str
    BirthDate: str
    CountryCode: Optional[str] = None