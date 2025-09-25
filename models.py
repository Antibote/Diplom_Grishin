from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column

from database.db import Base

class User(Base):
    __tablename__ = "Users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)

    items = relationship("Item", back_populates="category")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    quantity = Column(Integer, nullable=False, default=0)
    price = Column(Float, nullable=False, default=0.0)

    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="items")