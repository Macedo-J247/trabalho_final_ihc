from pydantic import BaseModel, EmailStr
from typing import Optional, List


# ---------- Usuário ----------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    role: Optional[str] = "client"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str] = None
    role: str

    class Config:
        orm_mode = True

# ---------- Merchant ----------
class MerchantCreate(BaseModel):
    store_name: str

class MerchantOut(BaseModel):
    id: int
    user_id: int
    store_name: str
    verified: bool

    class Config:
        orm_mode = True

# ---------- Tag (restrição alimentar) ----------
class TagCreate(BaseModel):
    code: str
    label: str

class TagOut(BaseModel):
    id: int
    code: str
    label: str

    class Config:
        orm_mode = True

# ---------- Product ----------
class ProductCreate(BaseModel):
    merchant_id: int
    name: str
    description: Optional[str] = None
    price: float = 0.0
    # lista de códigos de tag (ex: ["gluten_free","vegan"])
    tags: Optional[List[str]] = []

class ProductOut(BaseModel):
    id: int
    merchant_id: int
    name: str
    description: Optional[str] = None
    price: float
    active: bool
    tags: List[TagOut] = []

    class Config:
        orm_mode = True
