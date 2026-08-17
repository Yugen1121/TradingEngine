from wal.OrderWalWriter import OrderWalWriter
from utils.orderBookBuilder import OrderBookBuilder
from Models.model import OrderBookManager
from routes.ordersRoute import OrdersRoute
from utils.apiGateway import APIGateway
from wal.CommandLog import CommandLogWriter
from wal.recovery import Recovery

orderBook = OrderBookBuilder("./database.sqlite")
orderBookManager = OrderBookManager(orderBook)
walWriter = OrderWalWriter("order_wal_1.jsonl")
commandLogWriter = CommandLogWriter("commandlog_1.jsonl")
orderRoute = OrdersRoute(orderBookManager, walWriter, commandLogWriter)

extra_routes = {
    "/orders": orderRoute.order_handler
}

gateway = APIGateway(orderBook, orderBookManager ,extra_routes, walWriter)