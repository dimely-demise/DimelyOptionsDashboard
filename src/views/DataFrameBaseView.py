from model.DataFrameModel import DataFrameModel
import pandas as pd
import PyQt5 as qt

class DataFrameBaseView(qt.QtWidgets.QWidget):
    def __init__(self, columns=None, parent=None):
        super().__init__(parent)
        # Specify which columns to display
        self.columns_to_display = columns 
        # Create an instance of the model
        self.model: DataFrameModel = DataFrameModel(columns=self.columns_to_display)

    def update_data(self, source: pd.DataFrame, cols = None):


        self.model.setDataFrame(source)
        if (cols is not None):
            self.model.set_columns(cols)