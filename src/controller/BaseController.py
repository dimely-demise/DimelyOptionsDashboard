from typing import TypeVar, Generic, Type
from PyQt5.QtWidgets import QWidget

View = TypeVar('View', bound=QWidget)

class BaseController(Generic[View], QWidget):
    def __init__(self, view_cls: Type[View]):
        super().__init__()
        self.view = view_cls()  # Instantiate the view here
        self.setup()

    def setup(self):
        pass  # Add any setup code needed for all controllers here
