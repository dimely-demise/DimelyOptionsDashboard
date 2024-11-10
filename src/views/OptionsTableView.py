from PyQt5.QtWidgets import QTableView, QHBoxLayout, QWidget, QGridLayout, QPushButton,QAbstractItemView
import PyQt5 as qt
from model.DataFrameModel import DataFrameModel
import pandas as pd


class OptionsTableView(QWidget):
    def __init__(self, columns=None):
        super().__init__()
        self.tableView = QTableView()
        self.sidebar = QWidget()

        sidebar_layout = QHBoxLayout()
        self.sidebar.setLayout(sidebar_layout)

        self.connectButton: QPushButton = QPushButton(text="Verbinden")
        
        sidebar_layout.addWidget(self.connectButton)
        
        # Specify which columns to display
        self.columns_to_display = columns if columns else ['id', 'symbol', 'annual_return_rate', 'bid', 'ask', 'strike', 'undPrice', 'delta', 'IV', 'expiry', 'DTE', 'DTE2', 'latestUpdate']
        

        self.layout = QGridLayout()
        self.layout.addWidget(self.tableView, 0, 0)
        self.layout.addWidget(self.sidebar, 0, 1)
        self.setLayout(self.layout)

        self.layout.setColumnStretch(0, 8) 
        self.layout.setColumnStretch(1, 4)

         
        # Create an instance of the model
        self.model = DataFrameModel(columns=self.columns_to_display)
        self.tableView.setModel(self.model)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        self.tableView.doubleClicked.connect(self.onSelectionChanged)


    def update_data(self, source: pd.DataFrame):
        # Sort the DataFrame by 'latestUpdate' in ascending order before updating the model

        data = source[
            (source["otm_percentage"] >= 5) & 
            (source["bid"] >= 0.2) & 
            (source["delta"] >= -0.3) &
            (source["delta"] <= 0.3) &
            (source["IV"] <= 1)  & 
            (source["spread"] <= 0.05)
            ]

        self.model.setDataFrame(data.sort_values(by='annual_return_rate', ascending=False))

    def onSelectionChanged(self, index):
        row = index.row()
        row_data = self.model._data.iloc[row] 

        print(row_data)