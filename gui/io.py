from pathlib import Path
import json

import pandas as pd
from PySide2.QtWidgets import (
    QFileDialog,
    QTableWidgetItem
)


class IO:
    def __init__(self):
        self.path = None

    def save(self, matrix):
        if self.path is None:
            return self.save_as(matrix)
        self._write(matrix)

    def save_as(self, matrix):
        path, _ = QFileDialog.getSaveFileName(
            None, 'Save as', str(Path.home()), 'JSON (*.json)'
        )
        if path == '':
            return
        self.path = path.split('.')[0] + '.json'
        self._write(matrix)

    def _write(self, matrix):
        data = {
            'matrix': matrix.df.to_dict(),
            'value_score_df': matrix.value_score_df.to_dict(),
            'data_df': matrix.data_df.to_dict(),
        }
        with open(self.path, 'w') as f:
            f.write(json.dumps(data, indent=2))

    def open_(self, parent):
        path, _ = QFileDialog.getOpenFileName(
            None, 'Open file', str(Path.home()), 'JSON (*.json)'
        )
        if path == '':
            return

        with open(path, 'r') as f:
            data = json.load(f)

        # Order is significant
        # Duplicated because this clears the weights
        load_continuous_criteria(
            parent, pd.DataFrame.from_dict(data['data_df']).columns
        )

        parent.matrix.df = pd.DataFrame.from_dict(data['matrix'])
        load_criteria(parent)

        # Loading again because load_criteria has nasty side effects
        parent.matrix.df = pd.DataFrame.from_dict(data['matrix'])
        parent.matrix.value_score_df = pd.DataFrame.from_dict(data['value_score_df'])
        parent.matrix.data_df = pd.DataFrame.from_dict(data['data_df'])

        parent.matrix.continuous_criteria = parent.matrix.data_df.columns

        load_choices(parent)
        insert_weights(parent)
        insert_ratings(parent)
        insert_criterion_value_to_scores(parent)
        insert_data(parent)


def load_choices(parent):
    for choice in parent.matrix.df.index[1:]:
        parent.lineEdit.setText(choice)
        parent.pushButton.click()
        parent.matrix.df = parent.matrix.df[:-1]


def load_criteria(parent):
    parent.combo_box.setCurrentIndex(1)
    for criterion in parent.matrix.criteria:
        parent.lineEdit.setText(criterion)
        parent.pushButton.click()
    parent.combo_box.setCurrentIndex(0)


def load_continuous_criteria(parent, cc):
    for criterion in cc:
        parent.line_edit_cc_tab.setText(criterion)
        parent.criterion_button.click()


def insert_weights(parent):
    for idx, weight in enumerate(parent.matrix.df.loc['Weight'][:-1]):
        parent.matrix_widget.setItem(0, idx, QTableWidgetItem(str(weight)))


def insert_ratings(parent):
    for idx, (choice, series) in enumerate(parent.matrix.df.iloc[1:, :-1].iterrows()):
        row = idx + 1  # First row is weights
        for col, (criterion, rating) in enumerate(series.items()):
            if criterion in parent.matrix.continuous_criteria:
                continue
            parent.matrix_widget.setItem(row, col, QTableWidgetItem(str(rating)))
            parent.rating_changed(row, col)  # Update percentages


def insert_criterion_value_to_scores(parent):
    for row, series in parent.matrix.value_score_df.iterrows():
        for col_name, value in series.items():
            if col_name.endswith('_score'):
                criterion = col_name.split('_score')[0]
                parent.cc_tab_page.score_spin_boxes[criterion][int(row)].setValue(value)
            else:
                parent.cc_tab_page.value_spin_boxes[col_name][int(row)].setValue(value)


def insert_data(parent):
    for choice, series in parent.matrix.data_df.iterrows():
        for criterion, value in series.items():
            parent.data_tab_page.sliders[choice][criterion].setValue(value)


io = IO()
