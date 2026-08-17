import json
from contextlib import contextmanager
from Models.model import Orders
from functools import wraps

class CommandLogWriter:
    def __init__(self, filename: str = "commandlog_1.jsonl"):
        self.filename = filename
        self.f = open(self.filename, "a")
        
    async def insert(self, order: Orders):
        orderData = order.get_dict_info()
        data = {
            "action": "insert",
            "data": orderData
        }
        json.dump(data, self.f)
        self.f.write("\n")
        self.f.flush()
        print("after", self.f.tell())

    async def cancel(self, order: Orders):
        orderData = order.get_dict_info()
        data = {
            "action": "cancelled",
            "data": orderData
        }
        json.dump(data, self.f)
        self.f.write("\n")
        self.f.flush()

    async def write(self, action: str, order: Orders):
        if action == "cancelled":
            await self.cancel(order)

        elif action == "insert":
            await self.insert(order)

        else:
            return False
        return True