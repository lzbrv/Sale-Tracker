from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import declarative_base,relationship
from datetime import datetime
from sqlalchemy import text


Base = declarative_base()

class Item(Base):
    __tablename__="items"
    id=Column(Integer,primary_key=True, autoincrement=True)
    url=Column(Text, nullable=False,unique=True)
    site=Column(Text,nullable=False)
    name=Column(Text,nullable=True)
    current_price=Column(Float,nullable=True)
    check_every_minutes=Column(Integer,nullable=False,server_default=text("60"))
    next_check_at=Column(DateTime,nullable=False)
    status=Column(Text,nullable=False,server_default=text("'new'"))
    created_at=Column(DateTime,nullable=False,server_default=text("CURRENT_TIMESTAMP"))
    updated_at=Column(DateTime,nullable=False,server_default=text("CURRENT_TIMESTAMP"),server_onupdate=text("CURRENT_TIMESTAMP"))
    price_history=relationship("PriceHistory",back_populates="item")
    
    def __repr__(self):
        return f"<Item id={self.id} site={self.site!r} url={self.url!r}>"
    
class PriceHistory(Base):
    __tablename__="price_history"
    id=Column(Integer,primary_key=True,autoincrement=True)
    item_id=Column(Integer,ForeignKey("items.id"),nullable=False)
    price=Column(Float,nullable=True)
    in_stock=Column(Boolean,nullable=True)
    seen_at=Column(DateTime,nullable=False,server_default=text("CURRENT_TIMESTAMP"))
    item=relationship("Item",back_populates="price_history")

    def __repr__(self):
        return f"<PriceHistory id={self.id} item_id={self.item_id} price={self.price} in_stock={self.in_stock}>"