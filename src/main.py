import asyncio
import sys
import traceback
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget
import PyQt5.QtWidgets as QtWidgets
from controller.ScannerController import ScannerController
from infrastructure.Database import Database
from views.OptionsTableView import OptionsTableView
from controller.OptionsController import OptionsController
from qasync import QEventLoop
from ui.MainWindow_ui import Ui_MainWindow

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, loop: QEventLoop):
        super().__init__()
        self.setupUi(self)

        
        self.optionScanAnzeigen.triggered.connect(self.onLiveScanTriggered)
        self.underlyingScanAnzeigen.triggered.connect(self.onScannerTriggered)

        #self.setWindowTitle('Options Market Data Viewer')
        self.loop = loop  # Store the event loop for later use


        try:
            print("Initializing Database Connection")
            self.database = Database('127.0.0.1', 'root', 'dev', 'tws')  # Replace with actual credentials

            self.optionsDataController = OptionsController(self.database)
            self.scannerContriller = ScannerController(self.database)
            #self.controller.load_data()  # Load data and start the process

            #self.addTableViewToStack()


        except Exception as e:
            print("__init__",e)
            traceback.print_exc()
            QMessageBox.critical(self, "Database Connection Error", str(e))
            sys.exit(1)  # Exit the application if the database connection fails
             
    def onLiveScanTriggered(self):
        print("onLiveScanTriggered")
        self.content.setCurrentWidget(self.optionsDataController.view)

    def onScannerTriggered(self):
        print("onScannerTriggered")

        self.content.setCurrentWidget(self.scannerContriller.view)
    def clearContent(self):
        # Clear default pages 
        while self.content.count() > 0: 
            self.content.removeWidget(self.content.widget(0))

    def run(self):
        self.optionsDataController.load_data()  # Load data and start the process
        self.clearContent()

        self.content.addWidget(self.optionsDataController.view)
        self.content.addWidget(self.scannerContriller.view)

        self.onScannerTriggered()



    def closeEvent(self, event):
        self.optionsDataController.close()  # Close the controller on exit
        print("ontroller closed")
        self.loop.stop()
        print("loop  stopped")
        event.accept()  # Accept the close event
        print("ack event")
        sys.exit(0) 

if __name__ == '__main__':
    app = QApplication(sys.argv)
    loop = QEventLoop(app)  # Create an event loop for the QApplication
    asyncio.set_event_loop(loop)  # Set the loop for asyncio

    window = MainWindow(loop)
    window.show()
    window.run()
    window.showMaximized()

    
    
    try: 
        with loop: 
            loop.run_forever() 
    # Run the application 
    except (KeyboardInterrupt, SystemExit): 
        print("Exiting...") 
    finally: 
        loop.close() 
        sys.exit(0)
