import sqlite3

with open('schema.txt', 'r') as f:
    schema = f.read()

conn = sqlite3.connect("prices.db")
conn.executescript(schema)
conn.commit()
conn.close()
print("database initialized")