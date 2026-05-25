from pydantic import BaseModel
from typing import Optional

from app.integrations.corendon.schemas.common.payment import PaymentSchema, ContactInformationSchema


class BookingRequest(BaseModel):
    BasketKey: str
    OptionReservation: Optional[bool] = False
    SalesSourceCode: Optional[str] = ""
    BookingLanguageCode: Optional[str] = "EN"
    SalesAmount: str
    Payment: PaymentSchema
    ContactInformation: ContactInformationSchema

class OptionConfirmRequest(BaseModel):
    Pnr: str
    SalesAmount: str
    Payment: PaymentSchema

class ModifyRequest(BaseModel):
    Pnr: str