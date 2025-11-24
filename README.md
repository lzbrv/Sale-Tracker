Sale Tracker

A Python-powered price monitoring system that automatically scrapes SSENSE product prices, stores historical changes, schedules periodic checks, and sends email alerts when items drop 10% or more.
Built with Playwright, SQLAlchemy, SQLite, and Python’s email APIs.

📦 Features

Tracks product price & stock status from SSENSE

Stores full price history in SQLite

Automatic scheduling using next_check_at

Sends email alerts on significant price drops (≥10%)

Fully headless background worker

Persistent Playwright browser profile to bypass Cloudflare

Clean modular structure for easy extension

🚀 Quick Start
1. Clone the repository:
   
git clone https://github.com/lzbrv/Sale-Tracker.git
cd Sale-Tracker

3. Create and activate a virtual environment:
   
Windows (Command Prompt in VS Code):
python -m venv .venv
.venv\Scripts\activate.bat

macOS/Linux:
python3 -m venv .venv
source .venv/bin/activate

3. Install dependencies:

   
pip install sqlalchemy playwright python-dotenv bs4 lxml
python -m playwright install chromium

5. Create your .env file

Create a .env in the project root:

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
FROM_ADDR=your_email@gmail.com
TO_ADDR=recipient_email@gmail.com


Important: SMTP_PASS must be a Gmail App Password, not your regular Gmail password.
You can generate one in Google Account → Security → App Passwords.

5. Complete the initial Cloudflare bypass (“first scrape”)

SSENSE uses Cloudflare, so the first scrape must be non-headless.

Edit sale_tracker.py:

Set:

headless=False

Run a test scrape:
python -c "from sale_tracker import scrape; print(scrape('INSERT SSENSE URL HERE'))"


A real Chrome window will open → load → then return product JSON.

Then revert:
headless=True


Now scraping runs fully headless using saved cookies.

6. Initialize the database

Delete any old DB:

del prices.db      # Windows
rm prices.db       # macOS/Linux


Run worker once to auto-create tables:

python worker.py


Let it run 2–3 seconds, then stop with Ctrl+C.

7. Add an item to track
python add_item.py "INSERT SSENSE URL THAT YOU WANT TO TRACK HERE"


Expected output:

Added item ID: 1


Add as many items as you want.

8. Run the worker continuously
python worker.py


The worker will:

scrape due items

insert price history

update the item’s current_price

schedule the next check

send email alerts on 10%+ drops

Silence is normal when no items are due — it’s sleeping intentionally.

🗃️ Database Inspection Commands
Show all tracked items:
python -c "import sqlite3; conn=sqlite3.connect('prices.db'); print(conn.execute('select * from items').fetchall())"

Show recent price history:
python -c "import sqlite3; conn=sqlite3.connect('prices.db'); print(conn.execute('select * from price_history order by seen_at desc limit 10').fetchall())"

🧱 Project Structure
Sale-Tracker/
│
├── worker.py              # background job loop
├── sale_tracker.py        # Playwright scraper
├── send_email.py          # email alert module
├── add_item.py            # add new items
├── models.py              # SQLAlchemy ORM models
├── database.py            # DB engine & session
├── .env                   # SMTP configuration (ignored by Git)
├── prices.db              # SQLite DB (auto generated)
└── ssense_profile/        # Playwright persistent profile

⚙️ Technologies Used

Python

Playwright (synchronous API)

BeautifulSoup / lxml

SQLAlchemy ORM

SQLite

dotenv

smtplib / email.message

📨 Price Drop Alert Example

When a price drops ≥10%, you’ll receive an email like:

Subject:

Price drop alert


Message:

Our Legacy Third Cut Jeans dropped from $260.00 to $220.00.
https://www.ssense.com/en-us/men/product/...

📎 Notes

Playwright stores cookies in ssense_profile/ so Cloudflare bypass only needs to happen once.

Worker is intentionally quiet unless debugging messages are added.

Default check interval is 60 minutes, configurable per item.
