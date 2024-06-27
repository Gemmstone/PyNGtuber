import copy

from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
from PyQt6.QtCore import QUrl, pyqtSignal, QThreadPool, pyqtSlot, QRunnable, QObject
import traceback
import asyncio
import sys
import re
import os


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(
                *self.args, **self.kwargs
            )
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class WebEnginePage(QWebEnginePage):
    failed_to_load_images = pyqtSignal()

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        if "update_images is not defined" in message or "addImagesToCanvas is not defined" in message:
            self.failed_to_load_images.emit()
            print("failed to load images, retrying...")
        else:
            print(
                f"javaScriptConsoleMessage: "
                f"level: '{level}' "
                f"message: '{message}' "
                f"lineNumber:  '{lineNumber}' "
                f"sourceID: '{sourceID}'"
            )


class LayeredImageViewer(QWebEngineView):
    loadFinishedSignal = pyqtSignal(bool)
    div_count_signal = pyqtSignal(str)
    failed_to_load_images = pyqtSignal()

    def __init__(self, exe_dir, hw_acceleration=False, parent=None):
        super(LayeredImageViewer, self).__init__(parent)
        self.res_dir = exe_dir
        self.obs_websocket = None
        page = WebEnginePage(self)
        page.failed_to_load_images.connect(self.failed_to_load_images.emit)
        self.setPage(page)
        self.html_code = ""
        self.setColor("#b8cdee")
        self.is_loaded = False
        self.loadFinished.connect(self.on_load_finished)

        self.threadpool = QThreadPool()

        self.oldIds = []

        self.update_settings(hw_acceleration=hw_acceleration)

        self.file = os.path.join(self.res_dir, 'Viewer', 'viewer.html')
        self.file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self.file)

        self.reload()

    def runJavaScript(self, js_code):
        self.page().runJavaScript(js_code)
        if self.obs_websocket is not None:
            try:
                asyncio.run(self.obs_websocket.send_js_command(js_code))
            except RuntimeError as err:
                print(err)

    def update_settings(self, hw_acceleration=False):
        settings = self.page().settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, hw_acceleration)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, hw_acceleration)

    def on_load_finished(self, result: bool):
        self.is_loaded = result
        self.loadFinishedSignal.emit(result)

    def setColor(self, color):
        self.page().runJavaScript(f'document.body.style.backgroundColor = "{color}";')

    def reload(self):
        self.is_loaded = False
        self.load(QUrl.fromLocalFile(self.file))
        self.is_loaded = True

        with open(self.file, 'r') as html_file:
            self.html_code = html_file.read()

    def updateImages(self, image_list=None, bg_color="#b8cdee", scale=100, edited=None, performance=False):
        images = copy.deepcopy(image_list)

        if images is not None:
            for layer in sorted(images, key=lambda x: x['posZ']):
                path_webp = os.path.basename(layer['route'])
                path_webp, uncompressed_extension = os.path.splitext(path_webp)
                path_webp = os.path.join(os.path.dirname(layer['route']), "webp", path_webp + ".webp")
                path_webp = str(os.path.join(self.res_dir, path_webp)).replace("\\", "/")
                if not os.path.isfile(path_webp):
                    path_webp = str(os.path.join(self.res_dir, layer["route"]))

                layer["routeOg"] = copy.deepcopy(layer["route"])
                layer["route"] = path_webp

            self.page().runJavaScript(f'document.body.style.backgroundColor = "{bg_color}";')
            self.runJavaScript(f'document.body.style.zoom = "{scale}%";')
            self.runJavaScript(f'addImagesToCanvas({str(images)}, {edited})')

    def get_animations(self, file_path, get_all=False):
        animation_names = []

        blacklist = ["onFinish", "play", "reset", "finish"]

        pattern = r'\b(\w+):\s*function'

        with open(file_path, 'r') as file:
            content = file.read()
            matches = re.findall(pattern, content)

            for match in matches:
                if match not in blacklist:
                    animation_names.append(match)

        return animation_names


