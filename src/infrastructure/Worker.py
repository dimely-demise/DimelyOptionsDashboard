from PyQt5.QtCore import QObject, pyqtSignal
from infrastructure.Database import Database
import pandas as pd

class Worker(QObject):
    update_signal = pyqtSignal(pd.DataFrame)

    def __init__(self, database: Database):
        super().__init__()
        self.database = database

    def run(self):
        data = self.database.get_options_watchlist()
        self.update_signal.emit(data)  # Emit the data once loaded
