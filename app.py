import websockets
import asyncio
import json


routes = {
    "/": print
}

async def handle_client(websocket):
    print("client connected")
    # check for message in websocket
    async for message in websocket:
        try:
            # check for json
            data = json.loads(message)
            # check for route
            route = data.get("route", "/")
            # get payload
            payload = data.get("payload", {})
            # check if the rout exists in the route map
            if route in routes:
                handler = routes[route]
                handler("hello world")
            response = {"status": "Success"}
        except json.JSONDecodeError:
            response = {"status": "Failed", "error": "INVALID PAYLOAD"}
        except Exception as e:
            response = {"status": "Failed", "error": str(e)}
        
        await websocket.send(json.dumps(response))

async def main():
    host = "127.0.0.1"
    port = 8000
    async with websockets.serve(handle_client, host=host, port=port):
        print(f"websocketserver running on {host}/{port}")
        await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())