# endpoints/tags.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/tags", tags=["tags"])

# helper simples: checa role admin
def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a administradores")
    return current_user

@router.post("/", response_model=schemas.TagOut, status_code=201)
def create_tag(payload: schemas.TagCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Cria uma tag de restrição alimentar.
    Por enquanto qualquer usuário autenticado pode criar; se quiser, trocamos para admin-only.
    """
    existing = db.execute(select(models.DietaryTag).where(models.DietaryTag.code == payload.code)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Tag já existe")
    tag = models.DietaryTag(code=payload.code, label=payload.label)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

@router.get("/", response_model=list[schemas.TagOut])
def list_tags(db: Session = Depends(get_db)):
    tags = db.execute(select(models.DietaryTag)).scalars().all()
    return tags

@router.put("/{tag_id}", response_model=schemas.TagOut)
def update_tag(tag_id: int, payload: schemas.TagCreate, db: Session = Depends(get_db), _admin: models.User = Depends(require_admin)):
    """
    Atualiza uma tag (code e label). Somente admin pode acessar.
    """
    tag = db.execute(select(models.DietaryTag).where(models.DietaryTag.id == tag_id)).scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada")
    # checar se novo code conflita com outra tag
    if payload.code != tag.code:
        conflict = db.execute(select(models.DietaryTag).where(models.DietaryTag.code == payload.code)).scalar_one_or_none()
        if conflict:
            raise HTTPException(status_code=400, detail="Outra tag com esse code já existe")
    tag.code = payload.code
    tag.label = payload.label
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

@router.delete("/{tag_id}", status_code=204)
def delete_tag(tag_id: int, db: Session = Depends(get_db), _admin: models.User = Depends(require_admin)):
    """
    Remove a tag. Somente admin.
    Atenção: se tag estiver associada a produtos, ela será desassociada automaticamente pelo SQLAlchemy.
    """
    tag = db.execute(select(models.DietaryTag).where(models.DietaryTag.id == tag_id)).scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada")
    db.delete(tag)
    db.commit()
    return None
