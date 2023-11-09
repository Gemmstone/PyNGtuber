
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
from PyQt6.QtCore import QCoreApplication, pyqtSignal
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QUrl
from PyQt6 import QtWidgets
import sys
import os


# LOCAL VARIABLES
app_name = ""
app_icon = ""
html_file = "www.youtube.com"


class LayeredImageViewer(QWebEngineView):
    loadFinishedSignal = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(LayeredImageViewer, self).__init__(parent)
        self.loadFinished.connect(self.on_load_finished)
        self.is_loaded = False

        settings = self.page().settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)

    def on_load_finished(self, result: bool):
        self.is_loaded = result
        self.loadFinishedSignal.emit(result)

    def reload(self, html_file):
        self.is_loaded = False
        file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), html_file)
        self.load(QUrl.fromUserInput(html_file))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app_name, html_file):
        super().__init__()
        self.setWindowTitle(app_name)

        self.browser = LayeredImageViewer()
        self.browser.reload(html_file)

        self.setCentralWidget(self.browser)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    QCoreApplication.setApplicationName(app_name)

    window = MainWindow(app_name, html_file)

    window.setWindowIcon(QIcon(app_icon))
    window.show()

    app.exec()
