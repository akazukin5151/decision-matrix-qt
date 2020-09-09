from functools import partial

import numpy as np
import pandas as pd
from matrix import Matrix
from PySide2.QtCore import QCoreApplication, Qt
from PySide2.QtWidgets import (
    QWidget,
    QGridLayout,
    QTableWidgetItem,
    QLabel,
    QMessageBox,
    QCheckBox,
    QGroupBox,
    QVBoxLayout,
    QSpinBox,
    QSlider,
    QHBoxLayout,
)

from gui.setup import SetupUIMixin
from gui.wizard import AbstractDataTab, AbstractValueScoreLayout


_translate = QCoreApplication.translate


def safe_float(string, fallback: 'T' = None) -> 'Union[float, T]':
    try:
        return float(string)
    except ValueError:
        if fallback:
            return fallback
        return 0.0


class ValueScoreTab(AbstractValueScoreLayout):
    def __init__(self, other):
        super().__init__(other.cc_grid)
        self.matrix = other.matrix
        self.tab_1 = other.matrix_tab

    def initializePage(self, criteria):
        criteria_filtered = [
            x for x in criteria
            if x not in self.rows_for_each_criteria.keys()
        ]
        super().initializePage(criteria_filtered)


class DataTab(AbstractDataTab):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.matrix = parent.matrix

    def matrix_action(self, choice, _criterion, _value):
        super().matrix_action(choice, _criterion, _value)
        row = self.matrix.df.index.get_loc(choice)
        column = self.matrix.df.columns.get_loc(_criterion)
        item = QTableWidgetItem(str(self.matrix.df.loc[choice, _criterion]))
        self.parent.matrix_widget.setItem(row, column, item)
        self.parent.max_total_changed(column)


class MatrixTabMixin:
    # Tab 1
    ## Callbacks
    def cell_changed(self, row, column):
        # Prevent infinite recursion
        if column == self.matrix_widget.columnCount() - 1:
            return

        new = self.matrix_widget.item(row, column)
        if not new or not new.text().isdigit():
            return

        if row == 0:
            return self.max_total_changed(column)
        return self.rating_changed(row, column)

    def combo_changed(self, new_index):
        # Index 0 means choice, index 1 means criteria
        self.lineEdit.returnPressed.disconnect()
        self.pushButton.clicked.disconnect()

        if new_index == 0:
            self.lineEdit.returnPressed.connect(self.add_row)
            self.pushButton.clicked.connect(self.add_row)
            self.pushButton.setText(_translate("MainWindow", "Add row", None))
        else:
            self.lineEdit.returnPressed.connect(self.add_column)
            self.pushButton.clicked.connect(self.add_column)
            self.pushButton.setText(_translate("MainWindow", "Add column", None))

    def add_row(self):
        if not (new_row_name := self.lineEdit.text()):
            return

        current_row_count = self.matrix_widget.rowCount()
        self.matrix_widget.setRowCount(current_row_count + 1)

        # Put an empty item in the row header...
        self.matrix_widget.setVerticalHeaderItem(current_row_count, QTableWidgetItem())

        # Then set its text
        item = self.matrix_widget.verticalHeaderItem(current_row_count)
        item.setText(new_row_name)

        self.set_last_column_uneditable()
        self.set_continuous_cells_uneditable()
        self.lineEdit.clear()
        self.lineEdit.setFocus()

        # Add to data tab
        if type(self.data_grid.itemAt(0).widget()) == QLabel:
            self.data_grid.takeAt(0).widget().deleteLater()

        groupbox = QGroupBox(new_row_name)
        QVBoxLayout(groupbox)

        # Copied
        for criterion_name in self.matrix.continuous_criteria:
            inner_grid = QHBoxLayout()
            self.data_tab_page.add_row(inner_grid, new_row_name, criterion_name)
            groupbox.layout().addLayout(inner_grid)
            self.data_grid.addWidget(groupbox)

        self.data_grid.addWidget(groupbox)
        self.data_tab_groupboxes[new_row_name] = groupbox

        self.matrix.add_choices(new_row_name)

    def add_column(self):
        # New column will be second last column; last column is always Percentage
        # Add new column on the right, then copy the values in Percentage to the new column
        if not (new_col_name := self.lineEdit.text()):
            return

        # WARNING: column count starts from 1, but the column argument in setters start from 0!!!
        self.matrix_widget.setColumnCount(self.matrix_widget.columnCount() + 1)

        # Put an empty item in the header...
        empty = QTableWidgetItem()
        self.matrix_widget.setHorizontalHeaderItem(self.matrix_widget.columnCount() - 1, empty)

        # So that we can set the text of the new column
        last = self.matrix_widget.horizontalHeaderItem(self.matrix_widget.columnCount() - 1)
        last.setText(_translate("MainWindow", "Percentage", None))

        # Move all the values, flags will be kept
        col_count_0i = self.matrix_widget.columnCount() - 1
        new_col_pos = col_count_0i - 1
        for row in range(self.matrix_widget.rowCount()):
            self.matrix_widget.setItem(
                row, col_count_0i,
                self.matrix_widget.takeItem(row, new_col_pos)
            )


        # Rename the header of 'new' column as perceived by user to input
        new = self.matrix_widget.horizontalHeaderItem(new_col_pos)
        new.setText(new_col_name)

        self.lineEdit.clear()
        self.lineEdit.setFocus()

        self.matrix.add_criterion(new_col_name, weight=float('nan'))

    def delete_row(self):
        bottom_fn = lambda x: x.topRow()
        top_fn = lambda x: x.bottomRow()
        selected_ranges = self.delete_row_or_column(bottom_fn, top_fn, 'choice row', 0)
        if not selected_ranges:
            return

        deleted_rows = []
        for the_range in reversed(selected_ranges):
            rows = range(the_range.topRow(), the_range.bottomRow() + 1)
            for row in reversed(rows):
                # If weights row selected, do nothing silently
                if row != 0 and row not in deleted_rows:
                    self.matrix_widget.removeRow(row)
                    self.matrix.df.drop(self.matrix.df.index[row], inplace=True)
                    deleted_rows.append(row)

    def delete_column(self):
        percentage_col = self.matrix_widget.columnCount() - 1
        bottom_fn = lambda x: x.leftColumn()
        top_fn = lambda x: x.rightColumn()
        selected_ranges = self.delete_row_or_column(
            bottom_fn, top_fn, 'criteria column', percentage_col
        )
        if not selected_ranges:
            return

        deleted_columns = []
        for the_range in reversed(selected_ranges):
            cols = range(the_range.leftColumn(), the_range.rightColumn() + 1)
            for col in reversed(cols):
                if col != percentage_col and col not in deleted_columns:
                    self.matrix_widget.removeColumn(col)
                    self.matrix.df.drop(
                        self.matrix.df.columns[col], axis='columns', inplace=True
                    )
                    deleted_columns.append(col)


    ## Sub-routines
    def set_continuous_cells_uneditable(self):
        for continuous_idx, criterion in enumerate(self.matrix.all_criteria):
            if criterion in self.matrix.continuous_criteria:
                for row in range(1, self.matrix_widget.rowCount()):
                    self.set_cell_uneditable(row, continuous_idx)

    def max_total_changed(self, column):
        new_weight = self.matrix_widget.item(0, column)
        criterion_name = self.matrix_widget.horizontalHeaderItem(column)
        if new_weight and criterion_name:
            self.matrix.update_weight(criterion_name.text(), safe_float(new_weight.text()))

        self.update_percentage_display()
        max_total = self.matrix.df.loc['Weight'].sum() * 10
        item = QTableWidgetItem(str(max_total))
        last_col = self.matrix_widget.columnCount()
        self.set_item_uneditable(item, 0, last_col - 1)

    def rating_changed(self, row, column):
        new_rating = self.matrix_widget.item(row, column)
        choice = self.matrix_widget.verticalHeaderItem(row)
        criterion_name = self.matrix_widget.horizontalHeaderItem(column)
        if new_rating and criterion_name and choice:
            self.matrix.update_rating(choice.text(), criterion_name.text(), safe_float(new_rating.text()))

        self.update_percentage_display()

    def update_percentage_display(self):
        it = zip(self.matrix.df.loc[:, 'Percentage'][1:], range(1, self.matrix_widget.rowCount()))
        for value, row in it:
            item = QTableWidgetItem(str(round(value, 2)) + '%')
            if (last_col := self.matrix_widget.columnCount()):
                self.set_item_uneditable(item, row, last_col - 1)

    def delete_row_or_column(self, bottom_fn, top_fn, name, condition):
        selected_ranges = self.matrix_widget.selectedRanges()

        if len(selected_ranges) == 0:
            QMessageBox.warning(
                None, 'Nothing selected', 'No rows were selected',
                QMessageBox.Ok, QMessageBox.Ok
            )
            return

        # Multiple ranges or one range that spans multiple row/column
        message = f'Are you sure you want to remove all of the selected {name}s?'
        if len(selected_ranges) == 1:
            the_range = selected_ranges[0]
            if bottom_fn(the_range) == condition and top_fn(the_range) == condition:
                return

            # Only one range, so if both are the same then there's only one row/column
            if bottom_fn(the_range) == top_fn(the_range):
                message = f'Are you sure you want to remove this {name}?'

        msgbox = QMessageBox()
        msgbox.setIcon(QMessageBox.Question)
        msgbox.setText(message)
        msgbox.setInformativeText('This action cannot be undone (for now)!')
        msgbox.setStandardButtons(QMessageBox.Cancel | QMessageBox.Yes)
        msgbox.setDefaultButton(QMessageBox.Yes)
        cb = QCheckBox('Do not show this again')
        msgbox.setCheckBox(cb)
        # TODO: actually make this checkbox do something
        if msgbox.exec() == QMessageBox.Cancel:
            return
        return selected_ranges


class ValueScoreTabMixin:
    def __init__(self):
        # This is the only init function in any mixin class
        self.matrix = Matrix()
        self.cc_tab_page = None
        # Data tab stuff
        self.data_tab_page = DataTab(self)
        self.data_tab_groupboxes = {}  # For add_row in the other mixin
        self.sliders = []
        self.spin_boxes = []

    # Tab 2
    ## Callbacks
    def add_continuous_criteria(self):
        if not (criterion_name := self.line_edit_cc_tab.text()):
            return

        if not self.cc_tab_page:
            self.cc_tab_page = ValueScoreTab(self)

        if criterion_name not in self.matrix.continuous_criteria:
            self.matrix.continuous_criteria.append(criterion_name)

        self.cc_tab_page.initializePage(self.matrix.continuous_criteria)

        # Add criteria to the main tab
        self.lineEdit.setText(criterion_name)
        self.add_column()
        # Set rating cells for those criteria to be uneditable
        col = self.matrix_widget.columnCount() - 2
        for row in range(1, self.matrix_widget.rowCount()):
            self.set_cell_uneditable(row, col)

        self.line_edit_cc_tab.clear()
        self.line_edit_cc_tab.setFocus()

        # Add to data tab
        if type(self.data_grid.itemAt(0).widget()) == QLabel:
            return

        for choice, groupbox in self.data_tab_groupboxes.items():
            inner_grid = QHBoxLayout()
            self.data_tab_page.add_row(inner_grid, choice, criterion_name)
            groupbox.layout().addLayout(inner_grid)
            self.data_grid.addWidget(groupbox)


class Ui_MainWindow(SetupUIMixin, MatrixTabMixin, ValueScoreTabMixin):
    pass

