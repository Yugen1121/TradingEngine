import asyncio
import json
import time
import websockets

async def run_benchmark(total_orders=1000):
    uri = "ws://localhost:8000" # Your websocket port
    
    start_all = time.perf_counter()
    
    # Send orders continuously
    async with websockets.connect(uri) as ws:
        for i in range(total_orders):
            payload = {
                "route": "/orders",
                "payload": {
                    "id": i,
                    "user_id": 45,
                    "type": "buy",
                    "price": 52.00,
                    "stock": "AAPL",
                    "quantity": 5,
                    "orderType": "LIMIT"
                }
            }
            await ws.send(json.dumps(payload))
            # Receive ACK response
            response = await ws.recv()

    end_all = time.perf_counter()
    
    total_time = end_all - start_all
    ops_per_sec = total_orders / total_time
    
    print(f"Sent & Received {total_orders} requests in {total_time:.4f} seconds.")
    print(f"Throughput: {ops_per_sec:.2f} requests/second")

if __name__ == "__main__":
    asyncio.run(run_benchmark(1000))