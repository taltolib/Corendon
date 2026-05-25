from pydantic import BaseModel

class BookingResponse(BaseModel):
    status: str
    code: int = 0
    message: str = ""
    pnr: str = ""

class OptionConfirmResponse(BaseModel):
    status: str
    code: int = 0
    message: str = ""
    pnr: str = ""