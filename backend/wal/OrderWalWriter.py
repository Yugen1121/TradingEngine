import json
from contextlib import contextmanager
from Models.model import Orders
from functools import wraps

class OrderWalWriter:

    @staticmethod
    def inject_file(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with open("order_wal_1.jsonl", "a") as file:
                import os
                print("Writing WAL to:", os.path.abspath("order_wal_1.jsonl"))
                return func(file, *args, **kwargs)

        return wrapper

    @inject_file
    def insert(f, order: Orders):
        orderData = order.get_dict_info()
        data = {
            "action": "insert",
            "data": orderData
        }
        json.dump(data, f)
        f.write("\n")
        f.flush()
        print("after", f.tell())

    @inject_file
    def cancel(f, order: Orders):
        orderData = order.get_dict_info()
        data = {
            "action": "cancelled",
            "data": orderData
        }
        json.dump(data, f)
        f.write("\n")
        f.flush()
        print("after", f.tell())

    @inject_file
    def insert_line(f, line: dict):
        json.dump(line, f)
        f.write("\n")
    
    @inject_file
    def tarderd():
        pass

    def update():
        pass
