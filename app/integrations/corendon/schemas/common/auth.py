from pydantic import BaseModel


class AuthCredentials(BaseModel):
    client_id: str = "CAI/fxQKTKpe63"
    client_secret: str = "uCQA2eddtbXLlrrQ"
    username: str
    password: str
