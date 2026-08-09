from ..Models.model import OrderQueue

class MatchingEngine:
    def __init__(self, queue: OrderQueue, requestHandler, logger, responder):
        self.queue:  OrderQueue = queue
        