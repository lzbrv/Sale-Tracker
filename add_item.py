import sys
from datetime import datetime
from database import SessionLocal
from models import Item


#usage: python add_item.py "https://www.ssense.com/en-us/men/product/..."
def main():
    if len(sys.argv)!=2:
        print("Usage: python add_item.py <ssense_url>")
        return
    url = sys.argv[1]
    with SessionLocal() as session:
        exists=session.query(Item).filter(Item.url==url).first()
        if exists:
            print("URL already exists in database")
            return
        item=Item(
            url=url,
            site="ssense",
            status="new",
            next_check_at=datetime.now(),
        )
        session.add(item)
        session.commit()
        print("Added item ID: ", item.id)

if __name__=="__main__":
    main()