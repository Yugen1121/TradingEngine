from Models.model import OrderTree, OrderBookManager, Orders
from fastapi import WebSocket, WebSocketDisconnect
import json
from Models.model import OrderBookManager

class APIGateway:
    """
    Owns everything transport related:
    - user to server WebSocket connections
    - user registry
    - route dispatch
    - pushing orders back to the right client
    """

    def __init__(
        self,
        order_book: OrderTree,
        orderBookManager: OrderBookManager,
        extra_routes: dict[str, callable],
    ):
        self._order_book: dict[str, dict[str, OrderTree]] = order_book
        self._order_book_manager: OrderBookManager = orderBookManager

        # user_id -> set of WebSockets
        self._users: dict[int, set[WebSocket]] = {}

        self._route: dict[str, callable] = {
            "/": self.printD
        }

        self._route.update(extra_routes)

        self._order_book_manager.on_event(self._gateway_dispatch)

    async def printD(self, payload):
        return {
            "status": "success",
            "books": json.dumps([(i, self._order_book[i].get("name", "")) for i in self._order_book])
        }

    def _register_user(
        self,
        user_id: int,
        websocket: WebSocket
    ) -> None:
        self._users.setdefault(user_id, set()).add(websocket)

    def _unregister_user(
        self,
        user_id: int,
        websocket: WebSocket
    ) -> None:
        conns = self._users.get(user_id)

        if conns:
            conns.discard(websocket)

            if not conns:
                del self._users[user_id]

    async def _gateway_dispatch(
        self,
        order: Orders,
        event,
        detail
    ) -> None:
        conns = self._users.get(order._user_id)

        if not conns:
            return

        message = {
            "status": "event",
            "event": event,
            "detail": detail,
            "order_id": order._id,
            "order_status": order.status.value,
        }

        payload = json.dumps(message, default=str)

        disconnected = []

        for ws in conns.copy():
            try:
                await ws.send_text(payload)

            except Exception:
                disconnected.append(ws)

        for ws in disconnected:
            self._unregister_user(
                order._user_id,
                ws
            )

    async def handle_client(
        self,
        websocket: WebSocket,
        user_id
    ) -> None:

        
        user_id = user_id
        

        if not user_id:
            await websocket.close(
                code=1008,
                reason="Missing user_id"
            )
            return

        await websocket.accept()
        self._register_user(
            user_id,
            websocket
        )

        try:
            while True:
                message = await websocket.receive_text()

                try:
                    data = json.loads(message)
                    
                    route = data.get("route", "")
                    payload = data.get("payload", {})

                    handler = self._route.get(route)

                    if handler is None:
                        response = {
                            "status": "failed",
                            "error": f"unknown route: {route}"
                        }
                    else:
                        response = await handler(payload)

                except json.JSONDecodeError:
                    response = {
                        "status": "failed",
                        "error": "invalid payload"
                    }

                except Exception as e:
                    response = {
                        "status": "failed",
                        "error": str(e)
                    }

                await websocket.send_text(
                    json.dumps(response, default=str)
                )

        except WebSocketDisconnect:
            pass

        finally:
            self._unregister_user(
                user_id,
                websocket
            )

