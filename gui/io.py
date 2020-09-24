from pathlib import Path
import json

import pandas as pd
from PySide2.QtWidgets import QFileDialog


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

        parent.matrix.df = pd.DataFrame.from_dict(data['matrix'])
        parent.matrix.value_score_df = pd.DataFrame.from_dict(data['value_score_df'])
        parent.matrix.data_df = pd.DataFrame.from_dict(data['data_df'])

        # TODO: populate values in table
        print(parent.matrix)
        print(parent.matrix.value_score_df)
        print(parent.matrix.data_df)

io = IO()
