from matrix import Matrix
from PySide2.QtCore import Qt, QMetaObject, QCoreApplication
from PySide2.QtGui import QKeySequence
from PySide2.QtWidgets import (
    QWidget,
    QTabWidget,
    QGridLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QMenuBar,
    QAction,
    QMenu,
)

from gui.wizard import WizardMixin


_translate = QCoreApplication.translate


class SetupUIMixin(WizardMixin):
    # Utils for both setup and tab 1
    def set_cell_uneditable(self, row, column):
        if not (item := self.matrix_widget.takeItem(row, column)):
            item = QTableWidgetItem()
        self.set_item_uneditable(item, row, column)

    def set_last_column_uneditable(self):
        if (col_count := self.matrix_widget.columnCount()):
            for row in range(self.matrix_widget.rowCount()):
                self.set_cell_uneditable(row, col_count - 1)

    def set_item_uneditable(self, item, row, column):
        flags = (
            Qt.ItemFlag.ItemIsSelectable,
            Qt.ItemFlag.ItemIsDragEnabled,
            Qt.ItemFlag.ItemIsDropEnabled,
            Qt.ItemFlag.ItemIsUserCheckable,
            Qt.ItemFlag.ItemIsEnabled,
        )

        for flag in flags:
            item.setFlags(flag)
        self.matrix_widget.setItem(row, column, item)

    # Setup
    ## Entry point
    def setupUi(self, MainWindow):
        self.main_window = MainWindow
        MainWindow.resize(771, 514)
        MainWindow.setWindowTitle(_translate("MainWindow", "Decision Matrix"))
        self.matrix = Matrix()

        self.centralwidget = QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)
        self.add_menubar(MainWindow)

        self.add_master_tabs()
        self.add_master_grid()

        # For matrix tab only
        self.add_input_bar()
        self.add_enter_button()
        self.add_combo_box()
        self.matrix_widget = self.add_table(tab=self.matrix_tab)
        self.matrix_widget = self.setup_table(self.matrix_widget)
        self.matrix_widget.verticalHeaderItem(0).setText("Weight")
        self.matrix_widget.horizontalHeaderItem(0).setText("Percentage")
        self.set_last_column_uneditable()
        self.add_matrix_tab_grid()
        self.matrix_widget.cellChanged["int", "int"].connect(self.cell_changed)

        # For data tab only
        self.add_criterion_button()
        self.add_input_bar_data_tab()
        self.add_inner_tab()
        self.add_data_tab_grid()

        # For actual data tab only
        self.add_data()

        self.set_tab_key_order()
        QMetaObject.connectSlotsByName(MainWindow)

    ## Subroutines
    def add_menubar(self, MainWindow):
        all_menus: 'dict[str, dict[str, dict[str, Union[func, QKeySequence, QAction]]]]'
        all_menus = {
            '&File': {
                '&Open': {
                    'shortcut': QKeySequence.Open,
                    'signal': lambda: print('todo'),
                },
                '&Save': {
                    'shortcut': QKeySequence.Save,
                    'signal': lambda: print('todo'),
                },
                'Save &as': {
                    'shortcut': QKeySequence.SaveAs,
                    'signal': lambda: print('todo'),
                },
                '&Quit': {
                    'shortcut': QKeySequence.Quit,
                    'role': QAction.QuitRole,
                    'signal': QCoreApplication.quit,
                },
            },
            '&Matrix': {
                '&Assistant': {
                    'shortcut': QKeySequence('Ctrl+A'),
                    'signal': self.init_wizard
                },
                '&Plot': {
                    'signal': lambda: print('todo'),
                },
                'Plot &interpolators': {
                    'signal': lambda: print('todo'),
                },
            },
            '&Help': {
                '&About': {
                    'role': QAction.AboutRole,
                    'signal': lambda: print('todo'),
                },
            },
        }
        menubar = QMenuBar(MainWindow)

        for menu_name, actions in all_menus.items():
            # Menubar and its menus
            menu = QMenu(menubar)
            menu.setTitle(menu_name)
            menubar.addAction(menu.menuAction())

            # Actions inside each menu
            for action_name, action_info in actions.items():
                action = QAction(MainWindow)
                action.setText(action_name)
                menu.addAction(action)

                menu_role = action_info.get('role', None)
                if menu_role:
                    action.setMenuRole(menu_role)

                shortcut = action_info.get('shortcut', None)
                if shortcut:
                    action.setShortcut(shortcut)

                signal = action_info.get('signal', None)
                if signal:
                    action.triggered.connect(signal)

        MainWindow.setMenuBar(menubar)

    def add_master_tabs(self):
        self.master_tab_widget = QTabWidget(self.centralwidget)
        self.matrix_tab = QWidget()
        self.continuous_criteria_tab = QWidget()
        self.data_tab = QWidget()
        self.master_tab_widget.addTab(self.matrix_tab, "Matrix")
        self.master_tab_widget.addTab(self.continuous_criteria_tab, "Continuous criteria")
        self.master_tab_widget.addTab(self.data_tab, "Data")

    def add_inner_tab(self):
        self.inner_tab_widget = QTabWidget(self.continuous_criteria_tab)

    def add_master_grid(self):
        self.app_grid_layout = QGridLayout(self.centralwidget)
        self.app_grid_layout.addWidget(self.master_tab_widget, 0, 0, 1, 1)

    def add_matrix_tab_grid(self):
        self.grid_layout = QGridLayout(self.matrix_tab)
        self.grid_layout.addWidget(self.combo_box, 0, 0, 1, 1)
        self.grid_layout.addWidget(self.lineEdit, 0, 1, 1, 1)
        self.grid_layout.addWidget(self.pushButton, 0, 2, 1, 1)
        self.grid_layout.addWidget(self.matrix_widget, 1, 0, 1, 3)

    def add_data_tab_grid(self):
        label = QLabel('Continuous criterion')
        self.continuous_criteria_tab_grid_layout = QGridLayout(self.continuous_criteria_tab)
        self.continuous_criteria_tab_grid_layout.addWidget(label, 0, 0, 1, 1)
        self.continuous_criteria_tab_grid_layout.addWidget(self.line_edit_data_tab, 0, 1, 1, 1)
        self.continuous_criteria_tab_grid_layout.addWidget(self.criterion_button, 0, 2, 1, 1)
        self.continuous_criteria_tab_grid_layout.addWidget(self.inner_tab_widget, 1, 0, 1, 3)

    def add_input_bar(self):
        self.lineEdit = QLineEdit(self.matrix_tab)
        self.lineEdit.returnPressed.connect(self.add_row)

    def add_input_bar_data_tab(self):
        self.line_edit_data_tab = QLineEdit(self.continuous_criteria_tab)
        self.line_edit_data_tab.returnPressed.connect(self.add_continuous_criteria)

    def add_enter_button(self):
        self.pushButton = QPushButton(self.matrix_tab)
        self.pushButton.setText('Add row')
        self.pushButton.clicked.connect(self.add_row)

    def add_criterion_button(self):
        self.criterion_button = QPushButton('Add')
        self.criterion_button.clicked.connect(self.add_continuous_criteria)

    def add_combo_box(self):
        self.combo_box = QComboBox(self.matrix_tab)
        self.combo_box.addItem("New choice")
        self.combo_box.addItem("New criteria")
        self.combo_box.currentIndexChanged.connect(self.combo_changed)

    def set_tab_key_order(self):
        QWidget.setTabOrder(self.master_tab_widget, self.combo_box)
        QWidget.setTabOrder(self.combo_box, self.lineEdit)
        QWidget.setTabOrder(self.lineEdit, self.pushButton)
        QWidget.setTabOrder(self.pushButton, self.matrix_widget)

        QWidget.setTabOrder(self.line_edit_data_tab, self.criterion_button)

    def add_table(self, tab):
        tableWidget = QTableWidget(tab)
        tableWidget.setGridStyle(Qt.SolidLine)
        tableWidget.setCornerButtonEnabled(True)
        tableWidget.horizontalHeader().setVisible(True)
        tableWidget.horizontalHeader().setCascadingSectionResizes(False)
        tableWidget.horizontalHeader().setSortIndicatorShown(False)
        tableWidget.verticalHeader().setVisible(True)
        tableWidget.setSortingEnabled(False)
        return tableWidget

    def setup_table(self, tableWidget):
        tableWidget.setColumnCount(1)
        tableWidget.setHorizontalHeaderItem(0, QTableWidgetItem())
        tableWidget.setRowCount(1)
        tableWidget.setVerticalHeaderItem(0, QTableWidgetItem())
        return tableWidget

    def add_data(self):
        self.data_grid = QGridLayout(self.data_tab)
        label = QLabel('There are no continuous criteria yet, add one in the second tab')
        self.data_grid.addWidget(label)
