from pydantic import BaseModel

from app.integrations.corendon.schemas.common.payment import PaymentSchema, ContactInformationSchema


class ModifySchemaBody(BaseModel):
    Pnr: str

class BookingCreateBody(BaseModel):
    BasketKey: str
    OptionReservation: bool | None = False
    SalesSourceCode: str | None = ""
    BookingLanguageCode: str | None = "EN"
    SalesAmount: str
    Payment: PaymentSchema
    ContactInformation: ContactInformationSchema

class OptionConfirmBody(BaseModel):
    Pnr: str
    SalesAmount: str
    Payment: PaymentSchema