from datetime import date
from pydantic import BaseModel, EmailStr

class SUserRegister(BaseModel):
    email: EmailStr
    password: str
    fullname: str
    username: str
    birthdate: date

class SUserAuth(BaseModel):
    email: EmailStr
    password: str