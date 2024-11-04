import asyncio
from ib_insync import IB, Contract, ScannerSubscription
from queue import Queue
import threading
from enum import Enum

class RequestType(Enum):
    MARKET_DATA = 'market_data'
    SCANNER = 'scanner'

class TwsRequestQueue:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TwsRequestQueue, cls).__new__(cls)
        return cls._instance

    def __init__(self, host='127.0.0.1', port=7497, clientId=1, max_requests: int = 90):
        if not hasattr(self, 'initialized'):  # Ensure __init__ runs only once
            self.ib = IB()
            self.host = host
            self.port = port
            self.clientId = clientId
            self.max_requests = max_requests
            self.queue = Queue(maxsize=max_requests)
            self.lock = threading.Lock()
            self.active_requests = {}
            self.reqId = 0
            self.connected = False  # Track connection status
            self.loop = asyncio.get_event_loop()
            
            asyncio.ensure_future(self.process_requests())
            self.initialized = True

    def connect_to_tws(self):
        if not self.connected:
            self.ib.connect(self.host, self.port, self.clientId)
            self.connected = True

    def add_request(self, contract: Contract):
        req_id = self.reqId
        self.reqId += 1
        with self.lock:
            if req_id not in self.active_requests:
                if not self.connected:
                    self.connect_to_tws()
                self.active_requests[req_id] = (RequestType.MARKET_DATA, contract)
                self.queue.put(req_id)

    def add_scanner_request(self, scanner: ScannerSubscription):
        req_id = self.reqId
        self.reqId += 1
        with self.lock:
            if req_id not in self.active_requests:
                if not self.connected:
                    self.connect_to_tws()
                self.active_requests[req_id] = (RequestType.SCANNER, scanner)
                self.queue.put(req_id)

    def cancel_request(self, req_id: int):
        with self.lock:
            if req_id in self.active_requests:
                request_type, _ = self.active_requests[req_id]
                if request_type == RequestType.MARKET_DATA:
                    self.ib.cancelMktData(req_id)
                elif request_type == RequestType.SCANNER:
                    self.ib.cancelScannerSubscription(req_id)
                del self.active_requests[req_id]

    def cancel_all_requests(self):
        for req_id in list(self.active_requests):
            self.cancel_request(req_id)
        self.active_requests.clear()

    async def process_requests(self):
        while True:
            req_id = await self.loop.run_in_executor(None, self.queue.get)
            request_type, request_data = self.active_requests[req_id]

            if request_type == RequestType.MARKET_DATA:
                self.loop.call_soon_threadsafe(self.ib.reqMktData, request_data, '', False, False)
            elif request_type == RequestType.SCANNER:
                self.loop.call_soon_threadsafe(self.ib.reqScannerSubscription, req_id, request_data)
            
            self.queue.task_done()
