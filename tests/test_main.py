import numpy as np
from unittest.mock import Mock, call
from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
    QTableWidgetItem
)

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
    assert 'apple' in ui.matrix.df.index

    qtbot.keyClicks(ui.lineEdit, 'orange')
    qtbot.keyClick(ui.lineEdit, Qt.Key_Enter)
    assert ui.matrix_widget.rowCount() == 3
    assert ui.matrix_widget.verticalHeaderItem(2).text() == 'orange'
    assert 'orange' in ui.matrix.df.index


def test_main_add_criteria(qtbot):
    MainWindow = QMainWindow()
    ui = main.Ui_MainWindow()
    qtbot.addWidget(ui)
    ui.setupUi(MainWindow)
    MainWindow.show()

    qtbot.mouseClick(ui.combo_box, Qt.LeftButton)
    qtbot.keyClick(ui.combo_box, Qt.Key_Down)
    qtbot.keyClick(ui.combo_box, Qt.Key_Enter)
    assert ui.combo_box.currentText() == 'New criteria'

    qtbot.keyClicks(ui.lineEdit, 'taste')
    assert ui.lineEdit.text() == 'taste'

    qtbot.mouseClick(ui.pushButton, Qt.LeftButton)
    assert ui.lineEdit.text() == ''
    assert ui.matrix_widget.columnCount() == 2
    assert ui.matrix_widget.horizontalHeaderItem(0).text() == 'taste'
    assert 'taste' in ui.matrix.df.columns

    qtbot.keyClicks(ui.lineEdit, 'color')
    qtbot.keyClick(ui.lineEdit, Qt.Key_Enter)
    assert ui.matrix_widget.columnCount() == 3
    assert ui.matrix_widget.horizontalHeaderItem(1).text() == 'color'
    assert 'color' in ui.matrix.df.columns


def test_main_weights(qtbot):
    MainWindow = QMainWindow()
    ui = main.Ui_MainWindow()
    qtbot.addWidget(ui)
    ui.setupUi(MainWindow)
    MainWindow.show()

    # Setup
    qtbot.keyClicks(ui.lineEdit, 'apple')
    qtbot.mouseClick(ui.pushButton, Qt.LeftButton)
    qtbot.keyClicks(ui.lineEdit, 'orange')
    qtbot.keyClick(ui.lineEdit, Qt.Key_Enter)

    qtbot.mouseClick(ui.combo_box, Qt.LeftButton)
    qtbot.keyClick(ui.combo_box, Qt.Key_Down)
    qtbot.keyClick(ui.combo_box, Qt.Key_Enter)

    qtbot.keyClicks(ui.lineEdit, 'taste')
    qtbot.mouseClick(ui.pushButton, Qt.LeftButton)

    qtbot.keyClicks(ui.lineEdit, 'color')
    qtbot.keyClick(ui.lineEdit, Qt.Key_Enter)

    # Neither clicks or tab key works
    ui.matrix_widget.setItem(0, 0, QTableWidgetItem('4'))
    assert ui.matrix.df.loc['Weight', 'taste'] == 4
    assert ui.matrix_widget.item(0, 2).text() == '40.0'
    assert ui.matrix_widget.item(1, 2).text() == '0.0%'
    assert ui.matrix_widget.item(2, 2).text() == '0.0%'


def test_main_ratings(qtbot):
    MainWindow = QMainWindow()
    ui = main.Ui_MainWindow()
    qtbot.addWidget(ui)
    ui.setupUi(MainWindow)
    MainWindow.show()

    # Setup
    qtbot.keyClicks(ui.lineEdit, 'apple')
    qtbot.mouseClick(ui.pushButton, Qt.LeftButton)
    qtbot.keyClicks(ui.lineEdit, 'orange')
    qtbot.keyClick(ui.lineEdit, Qt.Key_Enter)

    qtbot.mouseClick(ui.combo_box, Qt.LeftButton)
    qtbot.keyClick(ui.combo_box, Qt.Key_Down)
    qtbot.keyClick(ui.combo_box, Qt.Key_Enter)

    qtbot.keyClicks(ui.lineEdit, 'taste')
    qtbot.mouseClick(ui.pushButton, Qt.LeftButton)

    qtbot.keyClicks(ui.lineEdit, 'color')
    qtbot.keyClick(ui.lineEdit, Qt.Key_Enter)

    ui.matrix_widget.setItem(0, 0, QTableWidgetItem('4'))

    # Tests
    ui.matrix_widget.setItem(0, 1, QTableWidgetItem('7'))
    assert ui.matrix.df.loc['Weight', 'color'] == 7
    assert ui.matrix_widget.item(0, 2).text() == '110.0'
    assert ui.matrix_widget.item(1, 2).text() == '0.0%'
    assert ui.matrix_widget.item(2, 2).text() == '0.0%'

    ui.matrix_widget.setItem(1, 0, QTableWidgetItem('6'))
    assert ui.matrix.df.loc['apple', 'taste'] == 6
    assert ui.matrix_widget.item(1, 2).text() == '21.82%'

    ui.matrix_widget.setItem(1, 1, QTableWidgetItem('5'))
    assert ui.matrix.df.loc['apple', 'color'] == 5
    assert ui.matrix_widget.item(1, 2).text() == '53.64%'

    ui.matrix_widget.setItem(2, 0, QTableWidgetItem('9'))
    assert ui.matrix.df.loc['orange', 'taste'] == 9
    assert ui.matrix_widget.item(2, 2).text() == '32.73%'

    ui.matrix_widget.setItem(2, 1, QTableWidgetItem('3'))
    assert ui.matrix.df.loc['orange', 'color'] == 3
    assert ui.matrix_widget.item(2, 2).text() == '51.82%'


def test_tabs(qtbot):
    MainWindow = QMainWindow()
    ui = main.Ui_MainWindow()
    qtbot.addWidget(ui)
    ui.setupUi(MainWindow)
    MainWindow.show()

    assert ui.master_tab_widget.currentIndex() == 0
    # mouse click doesn't work
    ui.master_tab_widget.setCurrentIndex(1)
    assert ui.master_tab_widget.currentIndex() == 1


def test_add_continuous_criteria(qtbot):
    MainWindow = QMainWindow()
    ui = main.Ui_MainWindow()
    ui.setupUi(MainWindow)
    # Notice that QMainWindow is registered as the widget
    qtbot.addWidget(MainWindow)
    MainWindow.show()

    ui.master_tab_widget.setCurrentIndex(1)
    qtbot.keyClicks(ui.line_edit_data_tab, 'price')
    assert ui.line_edit_data_tab.text() == 'price'

    assert ui.inner_tab_widget.count() == 0
    qtbot.keyClick(ui.line_edit_data_tab, Qt.Key_Enter)
    assert ui.line_edit_data_tab.text() == ''
    assert ui.inner_tab_widget.count() == 1
    assert 'price' in ui.matrix.continuous_criteria

    table = ui.inner_tab_widget.currentWidget().layout().itemAt(0).widget()
    assert table.columnCount() == 2
    assert table.horizontalHeaderItem(0).text() == 'price'
    assert table.horizontalHeaderItem(1).text() == 'price_score'
    assert table.rowCount() == 1

    assert ui.inner_tab_widget.count() == 1
    qtbot.keyClicks(ui.line_edit_data_tab, 'size')
    qtbot.mouseClick(ui.criterion_button, Qt.LeftButton)  # Button works as well
    assert ui.inner_tab_widget.count() == 2
    assert 'size' in ui.matrix.continuous_criteria

    ui.inner_tab_widget.setCurrentIndex(1)
    table = ui.inner_tab_widget.currentWidget().layout().itemAt(0).widget()
    assert table.columnCount() == 2
    assert table.horizontalHeaderItem(0).text() == 'size'
    assert table.horizontalHeaderItem(1).text() == 'size_score'
    assert table.rowCount() == 1


def test_score_continuous_criterion(qtbot):
    MainWindow = QMainWindow()
    ui = main.Ui_MainWindow()
    ui.setupUi(MainWindow)
    # Notice that QMainWindow is registered as the widget
    qtbot.addWidget(MainWindow)
    MainWindow.show()

    # Setup
    ui.master_tab_widget.setCurrentIndex(1)
    qtbot.keyClicks(ui.line_edit_data_tab, 'price')
    #qtbot.keyClick(ui.line_edit_data_tab, Qt.Key_Enter)
    qtbot.mouseClick(ui.criterion_button, Qt.LeftButton)  # Button works as well
    table = ui.inner_tab_widget.currentWidget().layout().itemAt(0).widget()

    table.setItem(0, 0, QTableWidgetItem('0'))
    assert table.rowCount() == 1
    table.setItem(0, 1, QTableWidgetItem('10'))
    assert 'price' in ui.matrix.value_score_df.columns
    assert ui.matrix.value_score_df.loc[0, 'price'] == 0
    assert ui.matrix.value_score_df.loc[0, 'price_score'] == 10
    # After completing both columns, a new row automatically appears
    assert table.rowCount() == 2

    table.setItem(1, 0, QTableWidgetItem('10'))
    table.setItem(1, 1, QTableWidgetItem('5'))
    assert ui.matrix.value_score_df.loc[1, 'price'] == 10
    assert ui.matrix.value_score_df.loc[1, 'price_score'] == 5

    table.setItem(1, 1, QTableWidgetItem('9'))
    assert ui.matrix.value_score_df.loc[1, 'price_score'] == 9
    # Changing one cell does not affect everything else
    assert ui.matrix.value_score_df.loc[0, 'price'] == 0
    assert ui.matrix.value_score_df.loc[0, 'price_score'] == 10
    assert ui.matrix.value_score_df.loc[1, 'price'] == 10

