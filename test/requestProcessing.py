import asyncio
import time
from Models.model import Orders, RequestQueue, OrderBookManager, OrderType
from utils.requestHandler import RequestHandler
from utils.orderBookBuilder import OrderBookBuilder
import random
async def run_benchmark(total_orders=5000):  # Upped sample size for better stability
    uri = "ws://127.0.0.1:8000/?user_id=1" # Your websocket port

    queue = RequestQueue()
    payload = {
        "id": 104,
        "user_id": 45,
        "type": "buy",
        "price": 52.00,
        "stock": "AAPL",
        "quantity": 1,
        "order_type": OrderType.GTC
    }
    
    for i in range(total_orders):

        simulated_price = round(random.uniform(51.00, 53.00), 2)
    
        simulated_side = random.choice(["buy", "sell"])

        simulated_quantity = random.choice([1,2,3,4,5])
    
        queue.enqueue(Orders(
            i, 
            payload["user_id"], 
            simulated_side,            
            simulated_price,       
            payload["stock"], 
            simulated_quantity, 
            order_type=payload["order_type"]
        ))
        
    d = OrderBookManager(OrderBookBuilder("./database/database.sqlite"))
    handler = RequestHandler(d, queue, {})
    
    print(f"Starting benchmark for {total_orders} items...")
    start_all = time.perf_counter()
    handler.start()

    while queue.getLength() > 0 and handler.requests_processed < total_orders:
        await asyncio.sleep(0.005)  # Yields control so the processor thread runs at full speed
        
    end_all = time.perf_counter()
    
    total_time = end_all - start_all
    ops_per_sec = total_orders / total_time
    
    print("\n=== PERFORMANCE REPORT ===")
    print(f"Processed:  {total_orders} requests")
    print(f"Total Time: {total_time:.6f} seconds")
    print(f"Throughput: {ops_per_sec:.2f} requests/second")

if __name__ == "__main__":
    asyncio.run(run_benchmark(5000))