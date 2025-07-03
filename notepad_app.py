import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QAction, QFileDialog, QMessageBox, QTabWidget, QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QPainter, QTextBlock, QFontMetrics
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QIcon

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)

from PyQt5.QtCore import QSize

class TextEditWithLineNumbers(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path = None
        self.lineNumberArea = LineNumberArea(self)
        self.verticalScrollBar().valueChanged.connect(self.lineNumberArea.update)
        self.textChanged.connect(self.lineNumberArea.update)
        self.cursorPositionChanged.connect(self.lineNumberArea.update)
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def setFont(self, font):
        super().setFont(font)
        self.lineNumberArea.update()

    def lineNumberAreaWidth(self):
        digits = max(4, len(str(self.document().blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.cursorForPosition(QPoint(0, 0)).block()
        blockNumber = block.blockNumber()
        top = int(self.document().documentLayout().blockBoundingRect(block).top() - self.verticalScrollBar().value())
        bottom = top + int(self.document().documentLayout().blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top, self.lineNumberArea.width(), self.fontMetrics().height(),
                                 Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + int(self.document().documentLayout().blockBoundingRect(block).height())
            blockNumber += 1

class NotepadApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('PyQt5 Notepad')
        self.setGeometry(100, 100, 800, 600)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.update_line_char_count)
        self.setCentralWidget(self.tab_widget)
        self.create_menu_bar()
        self.create_status_bar()
        self.new_tab()
        self.update_line_char_count()

    def create_menu_bar(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu('File')

        new_action = QAction(QIcon(), 'New', self)
        new_action.setShortcut('Ctrl+N')
        new_action.setStatusTip('Create a new document')
        new_action.triggered.connect(self.new_tab)
        file_menu.addAction(new_action)

        open_action = QAction(QIcon(), 'Open...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Open an existing document')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction(QIcon(), 'Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.setStatusTip('Save the current document')
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction(QIcon(), 'Save As...', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.setStatusTip('Save the current document with a new name')
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction(QIcon(), 'Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit the application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View Menu
        view_menu = menubar.addMenu('View')

        zoom_in_action = QAction(QIcon(), 'Zoom In', self)
        zoom_in_action.setShortcut('Ctrl++')
        zoom_in_action.setStatusTip('Zoom in')
        zoom_in_action.triggered.connect(lambda: self.get_current_text_edit().zoomIn())
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction(QIcon(), 'Zoom Out', self)
        zoom_out_action.setShortcut('Ctrl+-')
        zoom_out_action.setStatusTip('Zoom out')
        zoom_out_action.triggered.connect(lambda: self.get_current_text_edit().zoomOut())
        view_menu.addAction(zoom_out_action)

        # Edit Menu
        edit_menu = menubar.addMenu('Edit')

        undo_action = QAction(QIcon(), 'Undo', self)
        undo_action.setShortcut('Ctrl+Z')
        undo_action.setStatusTip('Undo the last action')
        undo_action.triggered.connect(lambda: self.get_current_text_edit().undo())
        edit_menu.addAction(undo_action)

        redo_action = QAction(QIcon(), 'Redo', self)
        redo_action.setShortcut('Ctrl+Y')
        redo_action.setStatusTip('Redo the last action')
        redo_action.triggered.connect(lambda: self.get_current_text_edit().redo())
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction(QIcon(), 'Cut', self)
        cut_action.setShortcut('Ctrl+X')
        cut_action.setStatusTip('Cut the selected text')
        cut_action.triggered.connect(lambda: self.get_current_text_edit().cut())
        edit_menu.addAction(cut_action)

        copy_action = QAction(QIcon(), 'Copy', self)
        copy_action.setShortcut('Ctrl+C')
        copy_action.setStatusTip('Copy the selected text')
        copy_action.triggered.connect(lambda: self.get_current_text_edit().copy())
        edit_menu.addAction(copy_action)

        paste_action = QAction(QIcon(), 'Paste', self)
        paste_action.setShortcut('Ctrl+V')
        paste_action.setStatusTip('Paste text from clipboard')
        paste_action.triggered.connect(lambda: self.get_current_text_edit().paste())
        edit_menu.addAction(paste_action)

        # Help Menu
        help_menu = menubar.addMenu('Help')
        about_action = QAction(QIcon(), 'About', self)
        about_action.setStatusTip('About this application')
        about_action.triggered.connect(self.about_dialog)
        help_menu.addAction(about_action)

    def update_line_char_count(self):
        text_edit = self.get_current_text_edit()
        if text_edit:
            line_count = text_edit.document().blockCount()
            char_count = len(text_edit.toPlainText())
            self.line_char_count_label.setText(f'Lines: {line_count} | Chars: {char_count}')
        else:
            self.line_char_count_label.setText('')

    def create_status_bar(self):
        self.statusBar().showMessage('Ready')
        self.line_char_count_label = QLabel('')
        self.statusBar().addPermanentWidget(self.line_char_count_label)

    def new_tab(self):
        text_edit = TextEditWithLineNumbers()
        text_edit.file_path = None
        self.tab_widget.addTab(text_edit, "Untitled")
        self.tab_widget.setCurrentWidget(text_edit)
        text_edit.textChanged.connect(self.update_line_char_count)
        self.statusBar().showMessage('New tab created')
        self.setWindowTitle('PyQt5 Notepad - Untitled')

    def close_tab(self, index):
        if self.tab_widget.count() < 2:
            self.statusBar().showMessage("Cannot close the last tab.")
            return
        widget = self.tab_widget.widget(index)
        if widget is not None:
            widget.deleteLater()
        self.tab_widget.removeTab(index)
        self.statusBar().showMessage('Tab closed')

    def get_current_text_edit(self):
        return self.tab_widget.currentWidget()

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'Text Files (*.txt);;All Files (*)')
        if file_name:
            try:
                self.new_tab() # Create a new tab for the opened file
                text_edit = self.get_current_text_edit()
                with open(file_name, 'r') as f:
                    text_edit.setText(f.read())
                text_edit.file_path = file_name # Set file_path for the current tab
                self.statusBar().showMessage(f'Opened: {file_name}')
                self.setWindowTitle(f'PyQt5 Notepad - {file_name.split("/")[-1]}')
                self.tab_widget.setTabText(self.tab_widget.currentIndex(), file_name.split("/")[-1])
            except Exception as e:
                self.statusBar().showMessage(f'Error opening file: {e}')

    def save_file(self):
        text_edit = self.get_current_text_edit()
        if text_edit.file_path:
            try:
                with open(text_edit.file_path, 'w') as f:
                    f.write(text_edit.toPlainText())
                self.statusBar().showMessage(f'Saved: {text_edit.file_path}')
            except Exception as e:
                self.statusBar().showMessage(f'Error saving file: {e}')
        else:
            self.save_file_as()

    def save_file_as(self):
        file_name, _ = QFileDialog.getSaveFileName(self, 'Save File As', '', 'Text Files (*.txt);;All Files (*)')
        if file_name:
            try:
                text_edit = self.get_current_text_edit()
                with open(file_name, 'w') as f:
                    f.write(text_edit.toPlainText())
                text_edit.file_path = file_name
                self.statusBar().showMessage(f'Saved as: {file_name}')
                self.setWindowTitle(f'PyQt5 Notepad - {file_name.split("/")[-1]}')
                self.tab_widget.setTabText(self.tab_widget.currentIndex(), file_name.split("/")[-1])
            except Exception as e:
                self.statusBar().showMessage(f'Error saving file: {e}')

    def about_dialog(self):
        QMessageBox.about(self, 'About PyQt5 Notepad',
                          'This is a simple Notepad-like application built with PyQt5.')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = NotepadApp()
    editor.show()
    sys.exit(app.exec_())
