import asyncio
from datetime import datetime
import threading
from typing import List
from ib_insync import IB, Contract, Ticker
import numpy as np
import pandas as pd
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QTimer
from infrastructure.Database import Database
from views.OptionsTableView import OptionsTableView
from infrastructure.MarketDataQueue import MarketDataQueue
from infrastructure.TwsRequestQueue import TwsRequestQueue
from controller.BaseController import BaseController

class OptionsController(BaseController[OptionsTableView]):
    MAX_REQUESTS = 90  # Max simultaneous market data requests

    def __init__(self, database: Database) -> None:
        super().__init__(OptionsTableView)
        self.database = database
        #self.table_view = OptionsTableView()
        self.requestQueue = TwsRequestQueue()
        self.ib = self.requestQueue.ib
        self.lock = threading.RLock()



        self.full_dataframe: pd.DataFrame = pd.DataFrame()
        self.dataframe = pd.DataFrame(columns=['id', 'symbol', 'annual_return_rate', 'bid', 'ask', 'strike', 'expiry', 'undPrice', 'latestUpdate'])
       
        self.running = False  # Control the market data update loop

        # Connect the tick event to the handler
        self.ib.pendingTickersEvent += self.on_tick_received
        self.reqId = 0

        self.timer = QTimer()
        self.timer.setInterval(4000)  # 10 seconds
        self.timer.timeout.connect(lambda: asyncio.ensure_future(self.request_market_data()))

        self.updateTimer = QTimer()
        self.updateTimer.setInterval(60000)  # 10 seconds
        self.updateTimer.timeout.connect(lambda: asyncio.ensure_future(self.storeUpdates()))

        self.view.connectButton.clicked.connect(self.connectTws)


    def connectTws(self):
        # Connect to IB
        # self.ib.connect('127.0.0.1', 7496, clientId=1)
        #self.ib.reqMarketDataType(4)


        self.timer.start()
        self.updateTimer.start()


    def load_data(self) -> None:       
        print("Loading data") 
        self.full_dataframe = self.database.get_options_watchlist()
        self.enhanceDataFrame()

        # Start market data requests
        #asyncio.ensure_future(self.start_market_data_requests())


        

    async def storeUpdates(self):
        print("Save this stuff")
        df = self.full_dataframe.copy()
        self.database.store_updates(df)
    
    def enhanceDataFrame(self):
        # Convert latestUpdate to datetime


        self.calculate_annual_return_rate()
        self.calculate_otm_distance()
        self.calculate_spread()

        print(datetime.now(), "Update View")
        # Emit a signal to update the UI
        self.view.update_data(self.full_dataframe) 

    def calculate_spread(self):
        with self.lock:
            self.full_dataframe["spread"] = np.where(
                self.full_dataframe['bid'].notnull() & self.full_dataframe['ask'].notnull(),
                self.full_dataframe['ask'] - self.full_dataframe['bid'],
                None
            )


    def calculate_annual_return_rate(self):
        with self.lock:
            self.full_dataframe['expiry'] = pd.to_datetime(self.full_dataframe['expiry'])
            today = datetime.now()
            self.full_dataframe['DTE2'] = (self.full_dataframe['expiry'] - today).dt.total_seconds() / 60 / 60 / 24
            
            # Calculate annual return rate
            self.full_dataframe['annual_return_rate'] = (
                (self.full_dataframe['bid'] / self.full_dataframe['strike']) * (365 / self.full_dataframe['DTE']) * 100
            )

    def calculate_otm_distance(self):
        with self.lock:
            self.full_dataframe['otm_distance'] = np.where(
                self.full_dataframe['undPrice'].notnull(),
                np.where(self.full_dataframe['optionTypeId'] == 1,
                        self.full_dataframe['strike'] - self.full_dataframe['undPrice'],  # Call option
                        self.full_dataframe['undPrice'] - self.full_dataframe['strike']),  # Put option
                None
            )
            self.full_dataframe['otm_percentage'] = np.where(
                self.full_dataframe['undPrice'].notnull(),
                np.where(self.full_dataframe['optionTypeId'] == 1,
                        (self.full_dataframe['strike'] - self.full_dataframe['undPrice']) / self.full_dataframe['undPrice'] * 100,  # Call option
                        (self.full_dataframe['undPrice'] - self.full_dataframe['strike']) / self.full_dataframe['undPrice'] * 100),  # Put option
                None
            )


    async def request_market_data(self) -> None:
        print("Starting market data requests:")
        with self.lock:
            # Update full_dataframe with the latest data from dataframe
            
            self.full_dataframe.update(self.dataframe)
            self.enhanceDataFrame()

            # Step 1: Get contracts with OTM distance >= 5% ordered by annual_return_rate
            eligible_contracts = self.full_dataframe[
                (self.full_dataframe['otm_percentage'].notnull()) & 
                (self.full_dataframe['otm_percentage'] >= 5) &
                (self.full_dataframe["bid"] >= 0.2) & 
                (self.full_dataframe["delta"] >= -0.3) &
                (self.full_dataframe["delta"] <= 0.3) &
                (self.full_dataframe["IV"] <= 1)  & 
                (self.full_dataframe["spread"] <= 0.05)
            ].nlargest(20, 'annual_return_rate')

            # Step 2: Get the oldest contracts to fill the remaining slots
            remaining_slots = self.MAX_REQUESTS - len(eligible_contracts)
            if remaining_slots > 0:
                oldest_remaining = self.full_dataframe.nsmallest(remaining_slots, 'latestUpdate')
                self.dataframe = pd.concat([eligible_contracts, oldest_remaining]).drop_duplicates()#.reset_index(drop=True)
            else:
                self.dataframe = eligible_contracts.reset_index(drop=True)

            # Delegate market data requests to MarketDataQueue
            current_contract_ids = set(self.dataframe['id'])
            for contract_id, req_id in list(self.requestQueue.active_requests.items()):
                if contract_id not in current_contract_ids:
                    self.requestQueue.cancel_request(req_id)
            
            # Request market data for the selected contracts
            for idx, row in self.dataframe.iterrows():
                contract_id = row['id']
                # print("Requesting ", row["symbol"], row['latestUpdate'])
                if contract_id not in self.requestQueue.active_requests:
                    contract = Contract(
                        conId=contract_id,
                        exchange='SMART',
                        currency='USD'
                    )

                    self.requestQueue.add_request(contract)

    def on_tick_received(self, tickers: List[Ticker]) -> None:
        # This method is called when market data ticks are received
        for ticker in tickers:
            # Use self.dataframe for the tick data updates
            index = self.dataframe.index[self.dataframe['id'] == ticker.contract.conId]
            # print("tick updates ", ticker.contract.conId, index)

            if not index.empty:
                # print("tick updates ", ticker.contract.symbol, ticker.bid)
                # Update the bid and ask prices
                self.dataframe.at[index[0], 'bid'] = ticker.bid if ticker.bid is not None else None
                self.dataframe.at[index[0], 'ask'] = ticker.ask if ticker.ask is not None else None
                self.dataframe.at[index[0], 'undPrice'] = ticker.modelGreeks.undPrice if ticker.modelGreeks  and ticker.modelGreeks.undPrice is not None else None
                self.dataframe.at[index[0], 'delta'] = ticker.modelGreeks.delta if ticker.modelGreeks and ticker.modelGreeks.delta is not None else None
                self.dataframe.at[index[0], 'IV'] = ticker.modelGreeks.impliedVol if ticker.modelGreeks and ticker.modelGreeks.impliedVol is not None else None
                self.dataframe.at[index[0], 'latestUpdate'] = pd.Timestamp.now()
                
                

    def close(self) -> None:
        # Cleanly close and stop all processes and timers
        #self.running = False
        print("Closing")
        self.timer.stop()
        self.updateTimer.stop()
        self.ib.pendingTickersEvent -= self.on_tick_received
        self.requestQueue.cancel_all_requests()
        self.database.close()
        self.ib.disconnect()
