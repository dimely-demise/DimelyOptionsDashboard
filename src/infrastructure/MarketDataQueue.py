import asyncio
from ib_insync import IB, Contract
from queue import Queue
import threading

class MarketDataQueue:
    def __init__(self, ib: IB, max_requests: int = 90):
        self.ib = ib
        self.max_requests = max_requests
        self.queue = Queue(maxsize=max_requests)
        self.lock = threading.Lock()
        self.active_requests = {}
        self.reqId = 0

        # Reference to the main event loop
        self.loop = asyncio.get_event_loop()
        asyncio.ensure_future(self.process_requests())

    def add_request(self, contract: Contract):
        req_id = self.reqId
        self.reqId += 1
        with self.lock:
            if req_id not in self.active_requests:
                self.active_requests[req_id] = contract
                self.queue.put(req_id)

    def cancel_request(self, req_id: int):
        with self.lock:
            if req_id in self.active_requests:
                self.ib.cancelMktData(req_id)
                del self.active_requests[req_id]

    def cancel_all_requests(self):
        for req_id in list(self.active_requests.values()):
            self.cancel_request(req_id)  # Cancels each active request
        self.active_requests.clear()  # Clear the active_requests dictionary

    async def process_requests(self):
        while True:
            req_id = await self.loop.run_in_executor(None, self.queue.get)
            contract = self.active_requests[req_id]
            
            # Schedule reqMktData to run in the main event loop
            self.loop.call_soon_threadsafe(self.ib.reqMktData, contract, '', False, False)
            self.queue.task_done()  # Mark the request as processed
