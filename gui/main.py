from functools import partial

import numpy as np
import pandas as pd
from PySide2.QtCore import QCoreApplication
from PySide2.QtWidgets import (
    QWidget,
    QGridLayout,
    QTableWidgetItem,
)

from gui.setup import SetupUIMixin


_translate = QCoreApplication.translate


def safe_float(string, fallback: 'T' = None) -> 'Union[float, T]':
    try:
        return float(string)
    except ValueError:
        if fallback:
            return fallback
        return 0.0


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

        self.matrix.add_criterion(new_col_name, weight=float('nan'))

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


class DataTabMixin:
    # Tab 2
    ## Callbacks
    def add_continuous_criteria(self):
        if not (criterion_name := self.line_edit_data_tab.text()):
            return

        # Add table inside inner tab
        table = self.add_table(tab=None)
        table = self.setup_table(table)
        table.setColumnCount(2)

        # Add the first column
        empty = QTableWidgetItem()
        table.setHorizontalHeaderItem(0, empty)
        last = table.horizontalHeaderItem(0)
        last.setText(criterion_name)

        # Add the second column
        empty = QTableWidgetItem()
        table.setHorizontalHeaderItem(1, empty)
        last = table.horizontalHeaderItem(1)
        last.setText(criterion_name + '_score')

        cb = partial(self.value_score_tab_cell_changed, table)
        table.cellChanged["int", "int"].connect(cb)

        # Add new tab
        new_tab = QWidget()
        self.inner_tab_widget.addTab(new_tab, criterion_name)
        # Add grid layout for the tab
        new_layout = QGridLayout(new_tab)
        # Put table in another tab
        new_layout.addWidget(table)
        # Switch to the new tab
        self.inner_tab_widget.setCurrentIndex(self.inner_tab_widget.currentIndex() + 1)

        self.line_edit_data_tab.clear()
        self.matrix.add_continuous_criterion(criterion_name, weight=float('nan'))

        # Add criteria to the main tab
        self.lineEdit.setText(criterion_name)
        self.add_column()
        # Set rating cells for those criteria to be uneditable
        col = self.matrix_widget.columnCount() - 2
        for row in range(1, self.matrix_widget.rowCount()):
            self.set_cell_uneditable(row, col)

    def value_score_tab_cell_changed(self, table, row, column):
        value = table.item(row, 0)
        score = table.item(row, 1)
        if not value or not score:
            return

        self.remove_last_row_if_last_two_empty(table)

        criterion = table.horizontalHeaderItem(0).text()
        value_f = safe_float(value.text(), np.nan)
        score_f = safe_float(score.text(), np.nan)

        # Row removed
        if value.text() == '' and score.text() == '':
            self.matrix.remove_criterion_value_to_score(row)
            print(self.matrix.value_score_df)
            return

        if len(self.matrix.value_score_df.columns) == 0:
            self.matrix.criterion_value_to_score(criterion, {value_f: score_f})
        else:
            # Think the API must support modifications by index
            # to avoid this.
            self.matrix.value_score_df.loc[row, criterion] = value_f
            self.matrix.value_score_df.loc[row, criterion + '_score'] = score_f

        print(self.matrix.value_score_df)

        # Add new row if both cells in the last row is full
        last_value = table.item(table.rowCount() - 1, 0)
        last_score = table.item(table.rowCount() - 1, 1)
        if last_value and last_score and last_value.text() != '' and last_score.text() != '':
            current_row_count = table.rowCount()
            table.setRowCount(current_row_count + 1)
            table.setVerticalHeaderItem(current_row_count, QTableWidgetItem())

    ## Subroutines
    def remove_last_row_if_last_two_empty(self, table):
        if table.rowCount() < 2:
            return

        last_value = table.item(table.rowCount() - 1, 0)
        last_score = table.item(table.rowCount() - 1, 1)
        second_last_value = table.item(table.rowCount() - 2, 0)
        second_last_score = table.item(table.rowCount() - 2, 1)
        # An empty cell can either be None or its text method returning ''
        if (
            (not last_value or last_value.text() == '')
            and (not last_score or last_score.text() == '')
            and (not second_last_value or second_last_value.text() == '')
            and (not second_last_score or second_last_score.text() == '')
        ):
            table.setRowCount(table.rowCount() - 1)


class Ui_MainWindow(SetupUIMixin, MatrixTabMixin, DataTabMixin):
    pass

