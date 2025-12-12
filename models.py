from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    post = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # <-- флаг администратора

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



class ActionType(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"

# models.py
class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("items.id", ondelete="SET NULL"), nullable=True)  # <- здесь
    action = Column(Enum(ActionType))
    description = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    item = relationship("Item", passive_deletes=True)

class Inventory(Base):
    __tablename__ = "inventories"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))

    items = relationship("InventoryItem", back_populates="inventory", cascade="all, delete-orphan")
    created_by_user = relationship("User")  # новая связь



class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id = Column(Integer, primary_key=True)
    inventory_id = Column(Integer, ForeignKey("inventories.id", ondelete="CASCADE"))
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"))

    expected_qty = Column(Integer, nullable=False)   # Ожидалось
    actual_qty = Column(Integer, nullable=True)     # Фактически
    difference = Column(Integer, nullable=True)

    inventory = relationship("Inventory", back_populates="items")
    item = relationship("Item")


