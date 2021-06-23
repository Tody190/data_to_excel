# -*- coding: utf-8 -*-
# author:yangtao
# time: 2021/06/22


import sys
import os

from Qt import QtWidgets
from Qt import QtGui
from Qt import QtCore

ICONS_DIRECTORY = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "icons")
)
print(ICONS_DIRECTORY)


class DropLineEdit(QtWidgets.QLineEdit):
    def __init__(self):
        super(DropLineEdit, self).__init__()
        self.setAcceptDrops(True)
        self.setDragEnabled(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super(DropLineEdit, self).dragEnterEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            url_object = event.mimeData().urls()[0]
            self.setText(url_object.toLocalFile())
        else:
            super(DropLineEdit, self).dropEvent(event)


class MainUI(QtWidgets.QWidget):
    def __init__(self):
        super(MainUI, self).__init__()
        self.settings = QtCore.QSettings("HZ", "version_downloader")

        self.__setup_ui()
        self.__retranslate_ui()

    def __setup_ui(self):
        self.main_window = QtWidgets.QVBoxLayout(self)

        # 信息框
        self.info_textedit = QtWidgets.QTextEdit()

        # 进度条
        self.dl_progressbar = QtWidgets.QProgressBar()
        self.dl_progressbar.setTextVisible(False)

        # 输出路径
        self.output_label = QtWidgets.QLabel()
        self.output_lineedit = DropLineEdit()
        self.output_layout = QtWidgets.QHBoxLayout()
        self.output_layout.addWidget(self.output_label)
        self.output_layout.addWidget(self.output_lineedit)

        # 下载按钮
        self.download_button = QtWidgets.QPushButton()

        self.main_window.addWidget(self.info_textedit)
        self.main_window.addWidget(self.dl_progressbar)
        self.main_window.addLayout(self.output_layout)
        self.main_window.addWidget(self.download_button)

    def __retranslate_ui(self):
        app_icon = QtGui.QIcon(os.path.join(ICONS_DIRECTORY, "app_icon.png"))
        self.setWindowIcon(app_icon)
        self.output_label.setText(u"导出路径")
        self.output_lineedit.setText(u"支持导出文件夹拖拽到此")
        self.download_button.setText(u"开始下载")

        # 设置窗口大小
        try:
            self.restoreGeometry(self.settings.value("mainwindow_geo"))
        except:
            pass

    def set_titile(self, text):
        self.setWindowTitle(text)

    def add_content(self, content):
        current_content = self.info_textedit.toPlainText()
        if current_content:
            self.info_textedit.insertPlainText("\n%s" % content)
        else:
            self.info_textedit.insertPlainText(content)
        self.info_textedit.moveCursor(QtGui.QTextCursor.End)

    def closeEvent(self, event):
        self.settings.setValue("mainwindow_geo", self.saveGeometry())


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MUI = MainUI()
    MUI.show()
    sys.exit(app.exec_())
