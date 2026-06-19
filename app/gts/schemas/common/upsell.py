from pydantic import BaseModel


class UpsellService (BaseModel) :
    name : str
    status : str
    status_name : str = ""
    is_bag : bool
    scode : str = ""

class Upsell (BaseModel) :
    name : str #- Незнаю
    services : list #- Незнаю

