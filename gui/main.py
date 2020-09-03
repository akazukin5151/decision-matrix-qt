from functools import partial

import numpy as np
import pandas as pd
from PySide2.QtCore import QCoreApplication
from PySide2.QtWidgets import (
    QWidget,
    QGridLayout,
    QTableWidgetItem,
    QLabel,
    QMessageBox,
    QCheckBox,
)

from gui.setup import SetupUIMixin
from gui.wizard import AbstractDataLayout


_translate = QCoreApplication.translate


def safe_float(string, fallback: 'T' = None) -> 'Union[float, T]':
    try:
        return float(string)
    except ValueError:
        if fallback:
            return fallback
        return 0.0


class DataTab(AbstractDataLayout):
    def __init__(self, grid, matrix):
        super().__init__(grid)
        self.matrix = matrix


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

        self.lineEdit.clear()
        self.lineEdit.setFocus()
        self.set_last_column_uneditable()
        self.set_continuous_cells_uneditable()

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


class DataTabMixin:
    # Tab 2
    ## Callbacks
    def add_continuous_criteria(self):
        if not (criterion_name := self.line_edit_data_tab.text()):
            return

        # Add to data tab
        page = DataTab(self.data_grid, self.matrix)
        page.initializePage([criterion_name])

        self.matrix.add_continuous_criterion(criterion_name, weight=float('nan'))

        # Add criteria to the main tab
        self.lineEdit.setText(criterion_name)
        self.add_column()
        # Set rating cells for those criteria to be uneditable
        col = self.matrix_widget.columnCount() - 2
        for row in range(1, self.matrix_widget.rowCount()):
            self.set_cell_uneditable(row, col)

        self.line_edit_data_tab.clear()
        self.line_edit_data_tab.setFocus()

# TODO: update calculated percentages from dataframe to table in tab 1
# TODO: sync with data tab in wizard


class Ui_MainWindow(SetupUIMixin, MatrixTabMixin, DataTabMixin):
    pass

