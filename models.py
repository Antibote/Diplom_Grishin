from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column

from database.db import Base

class User(Base):
    __tablename__ = "Users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]