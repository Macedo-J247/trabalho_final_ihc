# app/auth.py
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext


# MVP: chave fixa (você optou por praticidade). Troque depois.
SECRET_KEY = "chave-super-secreta-ihc-mvp-NAO-USAR_EM_PRODUCAO"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Força ident 2b (mais compatível) e mantém bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    # força o identificador 2b (evita detecção errada de backend em algumas plataformas)
    bcrypt__ident="2b"
)

MAX_BCRYPT_BYTES = 72  # bcrypt processa no máximo 72 bytes

def _normalize_password(password: str) -> bytes:
    # garante bytes e faz truncamento seguro até 72 bytes
    if isinstance(password, str):
        b = password.encode("utf-8")
    else:
        b = bytes(password)
    return b[:MAX_BCRYPT_BYTES]

def hash_password(password: str) -> str:
    pw = _normalize_password(password)
    # passlib aceita str ou bytes; passar bytes evita surpresas
    return pwd_context.hash(pw)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    pw = _normalize_password(plain_password)
    return pwd_context.verify(pw, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token
