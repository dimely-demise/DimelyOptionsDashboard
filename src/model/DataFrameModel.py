from PyQt5.QtCore import QAbstractTableModel, Qt
import pandas as pd

class DataFrameModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame = pd.DataFrame(), columns: list = None):
        super().__init__()
        self._data = df
        self._raw = df
        self._columns = columns if columns else df.columns.tolist()

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iat[index.row(), index.column()])
        return None

    def rowCount(self, index=None):
        return self._data.shape[0]

    def columnCount(self, index=None):
        return len(self._columns)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._columns[section])
            else:
                return str(section)  # Row headers
        return None

    def setDataFrame(self, df: pd.DataFrame):
        self.beginResetModel()
        self._raw = df
        self._data = df[self._columns]  # Use only the specified columns
        self.endResetModel()

    def set_columns(self, columns: list):
        self._columns = columns
        self.setDataFrame(self._raw)  # Refresh the data with the new column setup
