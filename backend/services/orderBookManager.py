from utils.orderBookBuilder import OrderBookBuilder
from Models.model import OrderBookManager
from routes.ordersRoute import OrdersRoute
from utils.apiGateway import APIGateway

orderBook = OrderBookBuilder("./database.sqlite")
orderBookManager = OrderBookManager(orderBook)
orderRoute = OrdersRoute(orderBookManager)

extra_routes = {
    "/orders": orderRoute.order_handler
}

gateway = APIGateway(orderBook, orderBookManager ,extra_routes)