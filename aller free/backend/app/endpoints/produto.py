# endpoints/produto.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from app.modelos import models
from app.esquemas import schemas
from app.query.database import get_db
from app.dependencias.dependencies import get_current_user, require_merchant


router = APIRouter(prefix="/products", tags=["products"])

# ---------- create product (já existente, mantém behavior) ----------
@router.post("/", response_model=schemas.ProductOut, status_code=201)
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db), current_user: models.User = Depends(require_merchant)):
    # verifica merchant
    merchant = db.execute(select(models.Merchant).where(models.Merchant.id == payload.merchant_id)).scalar_one_or_none()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant não encontrado")
    if merchant.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você não é o proprietário dessa loja")

    product = models.Product(
        merchant_id=payload.merchant_id,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        active=True
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # associa tags por code (se informadas)
    if payload.tags:
        tags_objs: List[models.DietaryTag] = []
        for code in payload.tags:
            tag = db.execute(select(models.DietaryTag).where(models.DietaryTag.code == code)).scalar_one_or_none()
            if not tag:
                raise HTTPException(status_code=404, detail=f"Tag '{code}' não encontrada")
            tags_objs.append(tag)
        product.tags = tags_objs
        db.add(product)
        db.commit()
        db.refresh(product)

    return product

# ---------- list products (filtrar por q e tag) ----------
@router.get("/", response_model=List[schemas.ProductOut])
def list_products(q: Optional[str] = None, tag: Optional[str] = Query(None, description="Filter by tag code"), db: Session = Depends(get_db)):
    stmt = select(models.Product)
    products = db.execute(stmt).scalars().all()

    if q:
        products = [p for p in products if q.lower() in (p.name or "").lower()]

    if tag:
        products = [p for p in products if any(t.code == tag for t in (p.tags or []))]

    return products

# ---------- get product by id ----------
@router.get("/{product_id}", response_model=schemas.ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.execute(select(models.Product).where(models.Product.id == product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return product

# ---------- list products by merchant (public) ----------
@router.get("/merchant/{merchant_id}", response_model=List[schemas.ProductOut])
def list_products_by_merchant(merchant_id: int, db: Session = Depends(get_db)):
    products = db.execute(select(models.Product).where(models.Product.merchant_id == merchant_id)).scalars().all()
    return products

# ---------- list products of current merchant (private) ----------
@router.get("/me", response_model=List[schemas.ProductOut])
def list_my_products(db: Session = Depends(get_db), current_user: models.User = Depends(require_merchant)):
    merchant = db.execute(select(models.Merchant).where(models.Merchant.user_id == current_user.id)).scalar_one_or_none()
    if not merchant:
        return []  # sem loja ainda
    products = db.execute(select(models.Product).where(models.Product.merchant_id == merchant.id)).scalars().all()
    return products

# ---------- add tags to a product ----------
@router.post("/{product_id}/tags", response_model=schemas.ProductOut)
def add_tags_to_product(product_id: int, tags: List[str], db: Session = Depends(get_db), current_user: models.User = Depends(require_merchant)):
    product = db.execute(select(models.Product).where(models.Product.id == product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    merchant = db.execute(select(models.Merchant).where(models.Merchant.id == product.merchant_id)).scalar_one_or_none()
    if merchant.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você não é o proprietário dessa loja")

    tags_objs: List[models.DietaryTag] = list(product.tags or [])
    for code in tags:
        tag = db.execute(select(models.DietaryTag).where(models.DietaryTag.code == code)).scalar_one_or_none()
        if not tag:
            raise HTTPException(status_code=404, detail=f"Tag '{code}' não encontrada")
        if tag not in tags_objs:
            tags_objs.append(tag)

    product.tags = tags_objs
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

# ---------- remove a tag from a product ----------
@router.delete("/{product_id}/tags/{tag_code}", response_model=schemas.ProductOut)
def remove_tag_from_product(product_id: int, tag_code: str, db: Session = Depends(get_db), current_user: models.User = Depends(require_merchant)):
    product = db.execute(select(models.Product).where(models.Product.id == product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    merchant = db.execute(select(models.Merchant).where(models.Merchant.id == product.merchant_id)).scalar_one_or_none()
    if merchant.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você não é o proprietário dessa loja")

    tag = db.execute(select(models.DietaryTag).where(models.DietaryTag.code == tag_code)).scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada")

    current_tags = list(product.tags or [])
    new_tags = [t for t in current_tags if t.id != tag.id]
    product.tags = new_tags
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

# ---------- partial update (PATCH) ----------
@router.patch("/{product_id}", response_model=schemas.ProductOut)
def update_product(product_id: int, payload: schemas.ProductCreate, db: Session = Depends(get_db), current_user: models.User = Depends(require_merchant)):
    """
    Atualização parcial usando ProductCreate (pode enviar subset dos campos).
    Só o proprietário pode atualizar.
    """
    product = db.execute(select(models.Product).where(models.Product.id == product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    merchant = db.execute(select(models.Merchant).where(models.Merchant.id == product.merchant_id)).scalar_one_or_none()
    if merchant.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você não é o proprietário dessa loja")

    # atualiza campos se fornecidos
    updated = False
    if payload.name is not None:
        product.name = payload.name
        updated = True
    if payload.description is not None:
        product.description = payload.description
        updated = True
    if payload.price is not None:
        product.price = payload.price
        updated = True
    if hasattr(payload, "tags") and payload.tags is not None:
        # se quiser sobrescrever tags totalmente:
        tags_objs = []
        for code in payload.tags:
            tag = db.execute(select(models.DietaryTag).where(models.DietaryTag.code == code)).scalar_one_or_none()
            if not tag:
                raise HTTPException(status_code=404, detail=f"Tag '{code}' não encontrada")
            tags_objs.append(tag)
        product.tags = tags_objs
        updated = True

    if updated:
        db.add(product)
        db.commit()
        db.refresh(product)

    return product

# ---------- delete product ----------
@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_merchant)):
    product = db.execute(select(models.Product).where(models.Product.id == product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    merchant = db.execute(select(models.Merchant).where(models.Merchant.id == product.merchant_id)).scalar_one_or_none()
    if merchant.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você não é o proprietário dessa loja")

    db.delete(product)
    db.commit()
    return None
