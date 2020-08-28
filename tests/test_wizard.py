from PySide2.QtCore import Qt
from unittest.mock import Mock, call

from gui import wizard


def test_choices_wizard_page(qtbot):
    w = wizard.Wizard()
    matrix = Mock()
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
