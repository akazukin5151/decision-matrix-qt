from PySide2.QtCore import Qt
from unittest.mock import Mock, call

from gui import wizard


class SubscriptableMock(Mock):
    subscripts = []

    def __getitem__(self, other):
        self.subscripts.append(other)


def test_choices_wizard_page(qtbot):
    w = wizard.Wizard()
    matrix = SubscriptableMock()
    w.matrix = matrix
    qtbot.addWidget(w)
    w.show()

    assert type(w.currentPage()) == wizard.WelcomePage

    qtbot.mouseClick(w.next_button, Qt.LeftButton)
    assert type(w.currentPage()) == wizard.ChoicesPage

    qtbot.keyClicks(w.currentPage().line_edit, 'apple')
    assert w.currentPage().line_edit.text() == 'apple'

    qtbot.keyClick(w.currentPage().line_edit, Qt.Key_Enter)
    assert w.currentPage().line_edit.text() == ''
    assert w.currentPage().list.item(0).text() == 'apple'

    qtbot.keyClicks(w.currentPage().line_edit, 'orange')
    qtbot.mouseClick(w.currentPage().add_button, Qt.LeftButton)
    assert w.currentPage().line_edit.text() == ''
    assert w.currentPage().list.item(1).text() == 'orange'
    assert w.currentPage().list.count() == 2

    assert w.matrix.method_calls == [
        call.add_choices('apple'),
        call.add_choices('orange')
    ]

    w.currentPage().list.setCurrentRow(1)
    qtbot.mouseClick(w.currentPage().delete_button, Qt.LeftButton)
    assert w.currentPage().list.count() == 1
    assert w.currentPage().list.item(0).text() == 'apple'

    assert w.matrix.subscripts == [2]
    assert len(w.matrix.method_calls) == 3
    # 'None' is because subscript mock returned None
    assert w.matrix.method_calls[-1] == call.df.drop(None, inplace=True)

    qtbot.mouseClick(w.next_button, Qt.LeftButton)
    assert type(w.currentPage()) == wizard.CriteriaPage

