from Models.model import OrderTree, OrderBookManager, Orders
from utils.orderBookBuilder import OrderBookBuilder
from routes.ordersRoute import OrdersRoute
import json
import websockets
import asyncio
import urllib
class APIGateway:
    """
    Owns everything transport related: user to server connection ( websockets ),
    limits users request, user registry, route dispatch, pushing orders back to the right client.
    """
    def __init__(self, order_book: OrderTree, 
                 orderBookManager: OrderBookManager, 
                 extra_routes: dict[str, callable], host: str = "127.0.0.1", port: int = 8000,
                 ):
        self._order_book: dict[str, dict[str, OrderTree]] = order_book
        self._order_Book_manager: OrderBookManager = orderBookManager
        self._users: dict[str, set] = {}
        self._host: str = host
        self._port: int = port

        self._loop: "asyncio.AbstractEventLoop | None" = None

        self._route: dict[str, callable] = {
            "/":  self.printD
        }

        self._route.update(extra_routes)

    async def printD(self, payload):
        print(self._order_book.keys())
        return {"status": "success", "books": list(self._order_book.keys())}

    def _register_user(self, user_id, websocket) -> None:
        self._users.setdefault(user_id, set()).add(websocket)

    def _unregister_user(self, user_id, websocket) -> None:
        conns = self._users.get(user_id)
        if conns:
            conns.discard(websocket)
            if not conns:
                del self._users[user_id]

    def _gateway_dispatch(self, order: Orders, event, detail) -> None:
        """
            callable function to respond to users
        """
        conns: websockets | None = self._users.get(order._user_id)
        if not conns:
            return

        message = {
            "status": "event",
            "even": event,
            "detail": detail,
            "order_id": order._id,
            "order_status": order.status.value,
        }

        payload = json.dumps(message, default=str)
        for ws in conns:
            future = asyncio.run_coroutine_threadsafe(ws.send(payload), self._loop)

            future.add_done_callback(lambda f, uid=order._user_id, sock=ws: self._on_send_result(f, uid, sock))

    def _on_send_result(self, future, uid, ws):
        try:
            future.result()
        except:
            self._unregister_user(uid, ws)


    async def handle_client(self, websocket) -> None:
        parsed_url = urllib.parse.urlparse(websocket.request.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        user_id = int(query_params.get("user_id")[0])
        
        if not user_id:
            print("Connection rejected: Missing user_id")
            await websocket.close(code=1008, reason="Missing user_id")
            return
        
        print("client connected")
        self._register_user(user_id, websocket)

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    route = data.get("route", "")
                    payload = data.get("payload", {})

                    handler = self._route.get(route)

                    if handler is None:
                        response = {"status": "failed", "error": f"unknown route: {route}"}
                    else:
                        response = await handler(payload)

                except json.JSONDecodeError:
                    response = {"status": "failed", "error": "invalid payload"}

                except Exception as e:
                    response  = {"status": "failed", "error": str(e)}

                await websocket.send(json.dumps(response))
        finally:
            self._unregister_user(user_id, websocket)
            print("client disconnected")

    async def start(self):
        self._loop = asyncio.get_running_loop()
        self._order_Book_manager.on_event(self._gateway_dispatch)

        async with websockets.serve(
            self.handle_client, 
            self._host, 
            self._port
            ):
            print(f"server running on {self._host}/{self._port}")
            await asyncio.get_running_loop().create_future()

async def main():
    order_book = OrderBookBuilder("./database/database.sqlite")
    order_book_manager = OrderBookManager(order_book)
    order_route = OrdersRoute(order_book_manager)

    extra_routes = {
        "/orders": order_route.order_handler
    }
 
    gateway = APIGateway(order_book, order_book_manager ,extra_routes)
    await gateway.start()

if __name__ == "__main__":
    asyncio.run(main())