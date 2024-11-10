import PyQt5.QtWidgets as qt
from model.DataFrameModel import DataFrameModel
from ui.ScannerView_ui import Ui_ScannerView
from views.DataFrameBaseView import DataFrameBaseView

class ScannerView(DataFrameBaseView, Ui_ScannerView):
    def __init__(self, columns=None):
        super().__init__(columns=columns)
        
        self.setupUi(self)
        
        self.tableView.setModel(self.model)
        #self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)