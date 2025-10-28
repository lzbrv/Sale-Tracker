import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

from database import engine,SessionLocal

load_dotenv()
SMTP_HOST=os.getenv("SMTP_HOST","smtp.gmail.com")
SMTP_PORT=int(os.getenv("SMTP_PORT","587"))
SMTP_USER=os.getenv("SMTP_USER")
SMTP_PASS=os.getenv("SMTP_PASS")
FROM_ADDR=os.getenv("FROM_ADDR") or SMTP_USER
TO_ADDR=os.getenv("TO_ADDR") or FROM_ADDR

def send_email(name,price,previousPrice,url):
    print([SMTP_HOST,SMTP_PORT,SMTP_USER,SMTP_PASS,FROM_ADDR,TO_ADDR])
    if not all([SMTP_HOST,SMTP_PORT,SMTP_USER,SMTP_PASS,FROM_ADDR,TO_ADDR]):
        raise RuntimeError("Missing SMTP config: Check your .env values")
    msg = EmailMessage()
    msg["From"]=FROM_ADDR
    msg["To"]=TO_ADDR
    msg["Subject"] = "Notification from Sale Tracker!"
    # msg.set_content(
    #     f"{name} dropped from ${previousPrice:.2f} to ${price:.2f}!\n"
    #     f"Link: {url}"
    # )
    msg["Subject"] = "Price drop alert"
    msg.set_content(
    f"{name} dropped from ${previousPrice:.2f} to ${price:.2f}.\n{url}\n"
        )
    msg.add_alternative(
    f"<p><b>{name}</b> dropped from ${previousPrice:.2f} to ${price:.2f}.</p>"
    f"<p><a href='{url}'>Open item</a></p>",
    subtype="html"
)
    with smtplib.SMTP(SMTP_HOST,SMTP_PORT) as s:
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(SMTP_USER,SMTP_PASS)
        s.send_message(msg)

if __name__ == "__main__":
    # quick local test
    send_email(
        name="OUR LEGACY Third Cut Jeans",
        price=149.00,
        previousPrice=180.00,
        url="https://example.com/product"
    
    )
    print("Email sent.")