from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.database import SessionLocal
from app import models, auth

# === Security scheme para o Swagger e extração do header Authorization ===
bearer_scheme = HTTPBearer(auto_error=True)  # faz o Swagger mostrar UM campo "Authorize"

# === DB session dependency ===
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === Helpers para token decode ===
def _decode_token_return_payload(token: str) -> dict:
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

# === Dependências de autenticação que seus endpoints devem usar ===
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """
    Extrai o token do header Authorization (Bearer ...) e devolve o User do DB.
    Aceita tanto "Bearer <token>" quanto apenas "<token>" (por precaução).
    """
    raw = credentials.credentials or ""
    token = raw.split()[-1] if raw.lower().startswith("bearer") else raw

    payload = _decode_token_return_payload(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sem subject")

    try:
        user_pk = int(user_id)
    except Exception:
        user_pk = user_id

    user = db.query(models.User).filter(models.User.id == user_pk).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")

    return user

def require_merchant(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    Garante que o usuário autenticado seja 'merchant'.
    """
    if getattr(current_user, "role", None) != "merchant":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a lojistas")
    return current_user
