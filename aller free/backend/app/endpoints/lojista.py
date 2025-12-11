from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.modelos import models
from app.esquemas import schemas
from app.query.database import get_db
from app.dependencias.dependencies import get_current_user


router = APIRouter(prefix="/merchants", tags=["merchants"])

@router.post("/", response_model=schemas.MerchantOut, status_code=201)
def create_merchant(
    payload: schemas.MerchantCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Cria uma merchant associada ao usuário autenticado.
    Se o usuário já tiver uma loja, retorna 400.
    Ao criar a loja, atualiza user.role -> 'merchant' e comita essa mudança.
    """
    # verifica se current_user já tem merchant
    existing = db.execute(
        select(models.Merchant).where(models.Merchant.user_id == current_user.id)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Usuário já tem uma loja")

    # cria merchant
    merchant = models.Merchant(user_id=current_user.id, store_name=payload.store_name)
    db.add(merchant)

    # atualiza role do usuário para 'merchant' (se já não for)
    if getattr(current_user, "role", None) != "merchant":
        current_user.role = "merchant"
        db.add(current_user)  # marca para atualização

    # efetiva tudo numa única transação
    db.commit()

    # refresh para retornar objetos com IDs atualizados
    db.refresh(merchant)
    db.refresh(current_user)

    return merchant

@router.get("/me", response_model=schemas.MerchantOut)
def get_my_merchant(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    merchant = db.execute(select(models.Merchant).where(models.Merchant.user_id == current_user.id)).scalar_one_or_none()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant não encontrado")
    return merchant
