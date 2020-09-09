from functools import partial

import numpy as np
from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QVBoxLayout,
    QPushButton,
    QSpinBox,
    QSizePolicy,
    QLabel,
    QFormLayout,
    QSlider,
)


class WizardMixin:
    def init_wizard(self):
        self.wizard = Wizard(self)
        self.wizard.rejected.connect(self.rejected)
        self.wizard.show()

    def rejected(self):
        #self.matrix = Matrix()
        #print(self.matrix)
        pass


class AbstractValueScoreLayout:
    def __init__(self, grid):
        # Subclasses must provide these attributes
        self.matrix: 'pd.DataFrame'
        self.tab_1: 'QWidget'

        self.grid = grid
        self.has_value = False
        self.has_score = False
        # Outer dict maps the criteria name to the last row
        self.rows_for_each_criteria: 'dict[str, int]' = {}
        # Mapping between criteria name to list of spinboxes
        self.value_spin_boxes: 'dict[str, list[QSpinBox]]' = {}
        self.score_spin_boxes: 'dict[str, list[QSpinBox]]' = {}

    def initializePage(self, criteria):
        # Maps each criteria to their vertical layouts
        self.vertical_layouts: 'dict[str, QVBoxLayout]' = {}

        # grid
        # |----> groupbox 1 (for criteria 1)
        #        |----> self.vertical_layout[0]
        #               |----> form 1 (for row 1)
        #                      |----> label
        #                      |----> inner_grid
        #                             |----> value_spin_box  # self.value_spin_boxes[criteria 1][0]
        #                             |----> label
        #                             |----> score_spin_box  # self.score_spin_boxes[criteria 1][0]
        #                             |----> delete_button
        #               |----> form 2 (for row 2)
        #                      |----> label
        #                      |----> inner_grid
        #                             |----> value_spin_box  # self.value_spin_boxes[criteria 1][1]
        #                             |----> label
        #                             |----> score_spin_box  # self.score_spin_boxes[criteria 1][1]
        #                             |----> delete_button
        #               |-... more forms...
        #               |----> add_new_pair_button
        # |----> groupbox 2 (for criteria 2)
        #        |----> self.vertical_layout[1]
        #               |-...
        for idx, criterion in enumerate(criteria):
            self.rows_for_each_criteria[criterion] = 0
            groupbox = QGroupBox(criterion)
            vertical_layout = QVBoxLayout(groupbox)
            self.vertical_layouts[criterion] = vertical_layout

            self.score_spin_boxes[criterion] = []
            self.value_spin_boxes[criterion] = []
            self.add_row(criterion, False)
            self.add_row(criterion, False)
            add_new_pair_button = QPushButton('&Add new pair')
            add_new_pair_button.clicked.connect(partial(self.add_row, criterion))

            vertical_layout.addWidget(add_new_pair_button, 0, alignment=Qt.AlignRight)

            self.grid.addWidget(groupbox)

    def value_changed(self, criterion, index, value):
        self.has_value = True
        if not self.has_score:
            return

        score = self.score_spin_boxes[criterion][index].value()
        self.update_matrix(value, score, criterion, index)

    def score_changed(self, criterion, index, score):
        self.has_score = True
        if not self.has_value:
            return

        value = self.value_spin_boxes[criterion][index].value()
        self.update_matrix(value, score, criterion, index)

    def update_matrix(self, value, score, criterion, index):
        if len(self.matrix.value_score_df.columns) == 0:
            self.matrix.criterion_value_to_score(criterion, {value: score})
        else:
            # Think the API must support modifications by index
            # to avoid this.
            self.matrix.value_score_df.loc[index, criterion] = value
            self.matrix.value_score_df.loc[index, criterion + '_score'] = score

        self.matrix._calculate_percentage()


    def add_row(self, criterion, deleteable=True):
        # The last row for this criterion
        index = self.rows_for_each_criteria[criterion]

        value_spin_box = QSpinBox()
        value_spin_box.setRange(0, 100)
        self.value_spin_boxes[criterion].append(value_spin_box)

        score_spin_box = QSpinBox()
        score_spin_box.setRange(0, 100)
        self.score_spin_boxes[criterion].append(score_spin_box)

        delete_button = QPushButton('&Delete')
        cb = partial(self.delete, criterion, index)
        delete_button.clicked.connect(cb)
        size_policy = QSizePolicy()
        size_policy.setRetainSizeWhenHidden(True)
        delete_button.setSizePolicy(size_policy)

        cb = partial(self.value_changed, criterion, index)
        value_spin_box.valueChanged.connect(cb)
        cb = partial(self.score_changed, criterion, index)
        score_spin_box.valueChanged.connect(cb)

        inner_grid = QGridLayout()
        inner_grid.addWidget(value_spin_box, index, 0)
        inner_grid.addWidget(QLabel('then score should be '), index, 1)
        inner_grid.addWidget(score_spin_box, index, 2)
        inner_grid.addWidget(delete_button, index, 3)
        if not deleteable:
            delete_button.hide()

        form = QFormLayout()
        form.addRow(QLabel('If ' + str(criterion) + ' is '), inner_grid)

        pos = self.vertical_layouts[criterion].count() - 1
        self.vertical_layouts[criterion].insertLayout(pos, form)

        # Increment the row number
        self.rows_for_each_criteria[criterion] += 1

    def delete(self, criterion, idx):
        pair = [criterion, criterion + '_score']
        self.matrix.value_score_df.loc[idx, pair] = np.nan
        self.rows_for_each_criteria[criterion] -= 1

        # Last item is the add button; get second last item
        form_pos = self.vertical_layouts[criterion].count() - 2
        # The form (row) to delete
        form = self.vertical_layouts[criterion].takeAt(form_pos)

        # Remove inner grid (second item in the form)
        inner_grid = form.takeAt(1)
        while (child := inner_grid.takeAt(0)):
            child.widget().deleteLater()
        del inner_grid
        self.value_spin_boxes[criterion].pop(idx)
        self.score_spin_boxes[criterion].pop(idx)

        # Remove form label (first item in the form)
        label = form.takeAt(0)
        label.widget().deleteLater()
        del label

        # Remove the form
        self.vertical_layouts[criterion].removeItem(form)


class AbstractDataTab:
    def __init__(self):
        self.sliders = {}
        self.spin_boxes = {}
        self.matrix: 'Matrix'  # Required

    def add_row(self, grid, choice, name):
        grid.addWidget(QLabel(str(name)), 0)

        spin_box = QSpinBox()
        spin_box.setRange(0, 10)
        cb = partial(self.spin_box_changed, choice, name)
        spin_box.valueChanged.connect(cb)
        if choice not in self.spin_boxes.keys():
            self.spin_boxes[choice] = {name: spin_box}
        else:
            self.spin_boxes[choice].update({name: spin_box})

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setMaximum(10)
        slider.setPageStep(1)
        slider.setTracking(True)
        cb = partial(self.slider_changed, choice, name)
        slider.valueChanged.connect(cb)
        if choice not in self.sliders.keys():
            self.sliders[choice] = {name: slider}
        else:
            self.sliders[choice].update({name: slider})

        grid.addWidget(spin_box, 1)
        grid.addWidget(slider, 2)

    def slider_changed(self, choice, criterion, value):
        self.spin_boxes[choice][criterion].setValue(value)
        self.matrix_action(choice, criterion, value)  # Only need to be triggered once

    def spin_box_changed(self, choice, criterion, value):
        self.sliders[choice][criterion].setValue(value)

    def matrix_action(self, choice, _criterion, _value):
        self.matrix.add_data(choice, {
            criterion: spin_box.value()
            for criterion, spin_box in self.spin_boxes[choice].items()
        })


