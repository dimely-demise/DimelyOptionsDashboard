from controller.BaseController import BaseController
from infrastructure.Database import Database
from infrastructure.TwsRequestQueue import TwsRequestQueue
from views.ScannerView import ScannerView
from ib_insync import ScanDataList
from typing import List
import pandas as pd

import ib_insync

class ScannerController(BaseController[ScannerView]):
    def __init__(self, database: Database) -> None:
        super().__init__(ScannerView)
        self.database = database
        #self.table_view = OptionsTableView()
        self.requestQueue = TwsRequestQueue()
        #Initialize an empty DataFrame with the required columns 
        self.scan_df = pd.DataFrame(columns=['reqId', 'rank', 'symbol', 'conId'])

        self.requestQueue.scan_received.connect(self.handleScan)

        scan_params = ib_insync.ScannerSubscription(
            instrument='STK',
            locationCode='STK.US.MAJOR',
            scanCode='HIGH_OPT_IMP_VOLAT_OVER_HIST'
        )

        self.requestQueue.add_scanner_request(scan_params)

    def handleScan(self, payload: ScanDataList): 
        data = payload
        # Iterate over the entries in the scan data 
        for entry in data: 
            reqId = data.reqId 
            rank = entry.rank 
            symbol = entry.contractDetails.contract.symbol 
            conId = entry.contractDetails.contract.conId 
            
            # Check if the entry with the same reqId and rank exists 
            if ((self.scan_df['reqId'] == reqId) & (self.scan_df['rank'] == rank)).any(): 
                # Update the existing entry 
                self.scan_df.loc[(self.scan_df['reqId'] == reqId) & (self.scan_df['rank'] == rank), ['symbol', 'conId']] = [symbol, conId] 
            else: 
                # Add a new entry to the DataFrame 
                new_row = pd.DataFrame({'reqId': [reqId], 'rank': [rank], 'symbol': [symbol], 'conId': [conId]}) 
                self.scan_df = pd.concat([self.scan_df, new_row], ignore_index=True)
                
        # Print the updated DataFrame for debugging 
        self.view.update_data(self.scan_df, self.scan_df.columns.tolist())
