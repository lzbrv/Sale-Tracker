from datetime import datetime, timedelta
import time

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from models import Base, Item, PriceHistory   # import your models
from sale_tracker import scrape # import your scraper

from database import engine,SessionLocal

from send_email import send_email

Base.metadata.create_all(engine)


''' worker.py will run in the background a check the prices.db for items that need to be updated
'''

#Step D
# returns items that need to be checked for a price update, doesn't return items if their status is "error" or "changed"
# returns items in ascending order of DateTime (earliest will be first) with items with null in next_check_at column first 
def get_due_items(session,limit=25):
    now = datetime.utcnow()
    stmt = (
        select(Item).
        where(
            (Item.next_check_at.is_(None)) | (Item.next_check_at<=now),
            (Item.status!="error") & (Item.status!="changed"),
        )
        .order_by(Item.next_check_at.nullsfirst())
        .limit(limit)
    )
    return list(session.scalars(stmt))


# schedules item's next_check_at and updates that the row has been touched, should be called after every processing 
def schedule_next(item):
    now = datetime.utcnow()
    next_check = now+timedelta(minutes=item.check_every_minutes)
    item.next_check_at=next_check
    item.updated_at=now


# records price history of item 
def record_price_history(session,item,price,in_stock_bool):
    ph = PriceHistory(
        item_id=item.id,
        price=float(price) if price is not None else None,
        in_stock=1 if in_stock_bool else 0
        #seen_at will default to current timestamp
    )
    session.add(ph)

#should be called before record_price_history() is called
def get_previous_price(session,item_id):
    row = session.scalars(select(PriceHistory.price)
                          .where(PriceHistory.item_id==item_id,PriceHistory.price!=None)
                          .order_by(PriceHistory.seen_at.desc())
                          .limit(1)
                          ).one_or_none()
    return row


def check_item(session,item):
    try:
        data = scrape(item.url)
        if not data:
            item.status="error"
            schedule_next(item)
            return
        
        #should check if data is none

        price = data.get("price")
        name = data.get("name")
        in_stock = data.get("in_stock")

        if (not item.name and name):
            item.name = name

        if (name and item.name and item.name!=name):
            item.status="changed"
        else:
            item.status="ok"

        if (price is not None):
            try:
                item.current_price=float(price)
            except (ValueError, TypeError):
                item.current_price=None

        previousPrice = get_previous_price(session,item.id)
        
        if (previousPrice and price and previousPrice > 0 and 100*((previousPrice-price)/previousPrice)>=10 and 
            all([item.name, item.current_price, item.url, previousPrice]) and item.status!="changed"):

            send_email(item.name,price,float(previousPrice),item.url)

        record_price_history(session,item,price,bool(in_stock))
        schedule_next(item)

    except Exception as e:
        item.status="error"
        schedule_next(item)

def run_once(batch_size=25):
    with SessionLocal() as session:
        items = get_due_items(session,limit=batch_size)
        if not items:
            return 0
        for item in items:
            check_item(session,item)
        session.commit()
        return (len(items))


def main():
    print("[worker] starting loop...")
    while True:
        processed=run_once(batch_size=25)
        if processed==0:
            time.sleep(10)
        else:
            time.sleep(1)
        
if __name__=="__main__":
    main()
        


    

