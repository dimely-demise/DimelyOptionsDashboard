import threading
import queue
from ib_insync import IB

class CommandQueue:
    def __init__(self):
        self.queue = queue.Queue()
        self.ib = IB()  # Initialize your IB client here
        self.worker_thread = threading.Thread(target=self.process_queue, daemon=True)
        self.worker_thread.start()

    def add_command(self, command, *args, **kwargs):
        self.queue.put((command, args, kwargs))

    def process_queue(self):
        while True:
            command, args, kwargs = self.queue.get()
            try:
                command(*args, **kwargs)
            except Exception as e:
                print(f"Error executing command {command}: {e}")
            finally:
                self.queue.task_done()

    def connect(self, host='127.0.0.1', port=7497, clientId=1):
        self.ib.connect(host, port, clientId)

    def request_market_data(self, symbol):
        self.add_command(self.ib.reqMktData, symbol)

    def place_order(self, contract, order):
        self.add_command(self.ib.placeOrder, contract, order)

# Usage example
command_queue = CommandQueue()
command_queue.connect()

# Request market data and place orders
command_queue.request_market_data('AAPL')
command_queue.place_order('AAPL Contract Object', 'Order Object')
