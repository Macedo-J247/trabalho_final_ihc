from sqlalchemy import Table, Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

# ---------- User ----------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # hash
    role = Column(String, default="client")  # client | merchant | admin
    name = Column(String, nullable=True)

# ---------- Merchant ----------
class Merchant(Base):
    __tablename__ = "merchants"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    store_name = Column(String, nullable=False)
    verified = Column(Boolean, default=False)

    user = relationship("User", backref="merchant")

# ---------- Product <-> Tag many-to-many ----------
product_tag_table = Table(
    "product_tag",
    Base.metadata,
    Column("product_id", Integer, ForeignKey("products.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("dietary_tags.id"), primary_key=True),
)

# ---------- DietaryTag ----------
class DietaryTag(Base):
    __tablename__ = "dietary_tags"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True)  # e.g. "gluten_free"
    label = Column(String, nullable=False)  # e.g. "Sem glúten"

    products = relationship("Product", secondary=product_tag_table, back_populates="tags")

# ---------- Product ----------
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, default=0.0)
    active = Column(Boolean, default=True)

    tags = relationship("DietaryTag", secondary=product_tag_table, back_populates="products")
