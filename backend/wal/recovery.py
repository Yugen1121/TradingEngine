import json
from Models.model import OrderBookManager, Orders

async def Recovery(g: OrderBookManager, wal) -> OrderBookManager:
    with open(wal, "r") as f:
        for line in f:
            try:
                data = json.loads(line)
                print(data)
                try:
                    order = Orders.mapper(data.get("data"))
                    print(order)
                    if order and data.get("action", None):
                        print(2)
                        await g.submit(order)
                    
                except KeyError:
                    print("Missing key")
            except Exception as e:
                print(e)
    return g