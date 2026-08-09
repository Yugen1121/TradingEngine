from Models.model import RequestQueue, OrderBookManager
from threading import Thread
from datetime import datetime
import time
class RequestHandler:
    def __init__(self, orderBook: OrderBookManager, requestQueue, logQueue):
        self._order_book: OrderBookManager = orderBook
        self._request_queue: RequestQueue = requestQueue
        self._logQueue_logQueue = logQueue
        self.running = True
        self.requests_processed = 0

        self._thread = Thread(target=self.process_request, 
                              daemon=True, 
                              name="RequestProcessingThread")
    
    def process_request(self):
        
        while self.running:
            order = self._request_queue.dequeue()
            if order:
                self._order_book.submit(order)
                print(self._order_book.books[order._stock][order._type].inorder(self._order_book.books[order._stock][order._type].root))
                self.requests_processed += 1
            else:
                time.sleep(0.001)

    def start(self):
        self._thread.start()


        