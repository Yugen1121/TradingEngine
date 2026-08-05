import sqlite3
from Models.model import OrderTree
def OrderBookBuilder(path) -> dict[str, dict[str, OrderTree]]:
    db = sqlite3.connect(path)

    cur = db.cursor()

    cur.execute("SELECT Name FROM stocks")

    d = {}
    for row in cur.fetchall():
        book = {"sell": OrderTree(), "buy": OrderTree()}
        d[row[0]] = book

    return d