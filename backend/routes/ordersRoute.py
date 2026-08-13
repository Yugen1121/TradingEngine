from Models.model import Orders, RequestQueueNode, RequestQueue, OrderBookManager, OrderType
from utils.requestHandler import RequestHandler
class OrdersRoute:
    """ Responsible for packaging and queuing the request """
    def __init__(self, orderBook: OrderBookManager):
        self._request_queue = RequestQueue()
        self._order_book: OrderBookManager = orderBook 
        self._request_handler = RequestHandler(orderBook, self._request_queue, {})
        self._next_id = 1
    # Map data into order object and push it to the request queue
    async def order_mapper(self, payload):
        # map the payload into an order
        # return the order
        try:
            side = payload["type"]
            if side not in ("buy", "sell"):
                raise ValueError(f"type must be 'buy' or 'sell', got {side!r}")
 
            raw_order_type = payload.get("order_type", "GTC")
            try:
                order_type = OrderType(raw_order_type)
            except ValueError:
                raise ValueError(f"invalid order_type: {raw_order_type!r}")

            return Orders(self.getNewId(), 
                          payload["user_id"], 
                          side,
                          payload["price"], 
                          payload["stock"], 
                          payload["quantity"], 
                          order_type=order_type)
        except KeyError as e:
            raise Exception("Key Error")

    async def order_handler(self, payload):
        # map the payload( order_mapper(payload))
        try:
            order = await self.order_mapper(payload)
            self._request_queue.enqueue(order)
            # push it into order queue
            response = {"status": "success", "message": "request accepted"}
        except Exception as e:
            response = {"status": "failed", "error": str(e)}
        return response

    def order_handler(self, order: Orders):
        if not isinstance(order, Orders):                
            raise TypeError
        self._request_queue.enqueue(order)
        return True

    def getNewId(self):
        temp = self._next_id
        self._next_id = self._next_id + 1
        return temp

    async def start(self):
        """Call this once, from async code, after the event loop is running."""
        self._request_handler.start()