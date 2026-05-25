from typing import Optional

from pydantic import BaseModel


class RefundReissue (BaseModel):
    status : Optional[str] #
    type : Optional[str] #
