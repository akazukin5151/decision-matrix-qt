import sys

from PySide2.QtWidgets import QApplication, QMainWindow

from gui import main


app = QApplication(sys.argv)
MainWindow = QMainWindow()
ui = main.Ui_MainWindow()
ui.setupUi(MainWindow)
MainWindow.show()
sys.exit(app.exec_())
