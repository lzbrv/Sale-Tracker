import sqlite3

conn = sqlite3.connect("prices.db")
cursor = conn.cursor()

# Show all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cursor.fetchall())

# Show columns for items
cursor.execute("PRAGMA table_info(items);")
print("Items columns:", cursor.fetchall())

# Show columns for price_history
cursor.execute("PRAGMA table_info(price_history);")
print("Price history columns:", cursor.fetchall())

conn.close()
