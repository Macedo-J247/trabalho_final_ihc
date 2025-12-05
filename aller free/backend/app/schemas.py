from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    ...


class LoginResponse(BaseModel):
    ...


class Usuario(BaseModel):
    ...


class UsuarioResponse(BaseModel):
    ...


class Lojista(BaseModel):
    ...


class LojistaResponse(BaseModel):
    ...


class Produto(BaseModel):
    ...


class ProdutoResponse(BaseModel):
    ...
