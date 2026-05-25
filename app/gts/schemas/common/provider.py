from typing import Optional

from pydantic import BaseModel


class Provider (BaseModel) :
    provider_id : str #- # Нужно скорей всего генерировать
    name :str #
    index : Optional[int] #
    type : str #
    is_charter : bool #
    provider_index : Optional[int] #
    supplier_id : str #
    supplier_name : str #

class SupplierProvider (BaseModel) :
    provider_name : str #
    provider_office : str #
