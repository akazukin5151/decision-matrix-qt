import numpy as np
from unittest.mock import Mock, call
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication, QMainWindow

from matrix import Matrix

from gui import main


def test_safe_float():
    assert main.safe_float('not a float') == 0.0
    assert main.safe_float('not a float', 10) == 10
    assert main.safe_float('2') == 2.0


def test_main_add_choices(qtbot):
    MainWindow = QMainWindow()
    ui = main.Ui_MainWindow()
    qtbot.addWidget(ui)
    ui.setupUi(MainWindow)
    MainWindow.show()

    qtbot.keyClicks(ui.lineEdit, 'apple')
    assert ui.lineEdit.text() == 'apple'

    qtbot.mouseClick(ui.pushButton, Qt.LeftButton)
    assert ui.lineEdit.text() == ''
    assert ui.matrix_widget.rowCount() == 2
    assert ui.matrix_widget.verticalHeaderItem(1).text() == 'apple'

    qtbot.keyClicks(ui.lineEdit, 'orange')
    qtbot.keyClick(ui.lineEdit, Qt.Key_Enter)
    assert ui.matrix_widget.rowCount() == 3
    assert ui.matrix_widget.verticalHeaderItem(2).text() == 'orange'
